"""File system watcher for automatic index updates."""

import asyncio
import queue
from pathlib import Path
from threading import Thread
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    DirDeletedEvent,
)

from semantic_mcp.config import Config
from semantic_mcp.services.indexer import Indexer


class CodeChangeHandler(FileSystemEventHandler):
    """Handles file system events for code files.

    Thread-safe design: File system events arrive on watchdog's worker thread.
    Events are marshalled to the asyncio event loop via a queue for processing.
    """

    def __init__(
        self,
        indexer: Indexer,
        config: Config,
        event_queue: asyncio.Queue | None = None,
    ):
        """Initialize handler.

        Args:
            indexer: Indexer service
            config: Configuration
            event_queue: AsyncQueue for marshalling events to event loop
        """
        self.indexer = indexer
        self.config = config
        self._event_queue = event_queue
        self._sync_queue: queue.Queue = queue.Queue()
        self._processor_thread: Thread | None = None
        self._stop_event = asyncio.Event()
        self._event_loop: asyncio.AbstractEventLoop | None = None

    def _is_code_file(self, path: str) -> bool:
        """Check if path matches code file patterns and is under target directory.

        Security: Validates file is within target directory to prevent path traversal.

        Args:
            path: File path to check

        Returns:
            True if path is a code file under target directory
        """
        try:
            path_obj = Path(path).resolve()
            target_dir = Path(self.config.target_dir).resolve()

            # Security: Ensure file is under target directory
            try:
                path_obj.relative_to(target_dir)
            except ValueError:
                return False  # File outside target directory

            return any(path_obj.match(pattern) for pattern in self.config.file_patterns)
        except (OSError, RuntimeError):
            return False  # Handle path resolution errors gracefully

    def _schedule_index(self, file_path: Path) -> None:
        """Schedule file for indexing - thread-safe.

        Puts file path on queue for processing by event loop thread.
        """
        self._sync_queue.put_nowait(str(file_path))

    async def _process_pending_files(self) -> None:
        """Process pending files from sync queue with debounce."""
        try:
            await asyncio.sleep(self.config.debounce_duration)
        except asyncio.CancelledError:
            return

        # Drain the queue
        files_to_index: list[str] = []
        while True:
            try:
                file_str = self._sync_queue.get_nowait()
                files_to_index.append(file_str)
            except queue.Empty:
                break

        if not files_to_index:
            return

        # Deduplicate
        files_to_index = list(set(files_to_index))

        for file_str in files_to_index:
            file_path = Path(file_str)
            if file_path.exists():
                await self.indexer.index_file(file_path)
            else:
                self.indexer.remove_file(file_path)

    def start(self, on_index_complete: Callable | None = None) -> None:
        """Start the async processor thread.

        Args:
            on_index_complete: Optional callback when indexing completes
        """
        async def processor():
            """Async processor that drains queue and indexes files."""
            while not self._stop_event.is_set():
                if not self._sync_queue.empty():
                    await self._process_pending_files()
                    if on_index_complete:
                        on_index_complete([])
                else:
                    await asyncio.sleep(0.1)  # Prevent busy loop

        def thread_target():
            """Run async processor in thread with dedicated event loop."""
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
            try:
                self._event_loop.run_until_complete(processor())
            finally:
                self._event_loop.close()
                self._event_loop = None

        self._processor_thread = Thread(target=thread_target, daemon=True)
        self._processor_thread.start()

    def stop(self) -> None:
        """Stop the processor thread."""
        self._stop_event.set()
        if self._processor_thread:
            self._processor_thread.join(timeout=5.0)
            self._processor_thread = None

    def on_modified(self, event):
        """Handle file modification."""
        if isinstance(event, FileModifiedEvent) and self._is_code_file(event.src_path):
            self._schedule_index(Path(event.src_path))

    def on_created(self, event):
        """Handle file creation."""
        if isinstance(event, FileCreatedEvent) and self._is_code_file(event.src_path):
            self._schedule_index(Path(event.src_path))

    def on_deleted(self, event):
        """Handle file deletion."""
        if isinstance(event, (FileDeletedEvent, DirDeletedEvent)):
            if self._is_code_file(event.src_path):
                self.indexer.remove_file(Path(event.src_path))


class WatcherService:
    """File system watcher service."""

    def __init__(self, config: Config, indexer: Indexer):
        """Initialize watcher.

        Args:
            config: Configuration
            indexer: Indexer service
        """
        self.config = config
        self.indexer = indexer
        self.observer: Observer | None = None
        self.handler: CodeChangeHandler | None = None

    def start(self, on_index_complete: Callable | None = None) -> None:
        """Start watching for file changes.

        Args:
            on_index_complete: Optional callback when indexing completes
        """
        target_path = Path(self.config.target_dir).resolve()

        self.handler = CodeChangeHandler(
            indexer=self.indexer,
            config=self.config,
        )
        self.handler.start(on_index_complete=on_index_complete)

        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(target_path),
            recursive=True,
        )
        self.observer.start()

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self.handler:
            self.handler.stop()
            self.handler = None
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

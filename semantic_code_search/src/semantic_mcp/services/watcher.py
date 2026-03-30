"""File system watcher for automatic index updates."""

import asyncio
from pathlib import Path
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
    """Handles file system events for code files."""

    def __init__(
        self,
        indexer: Indexer,
        config: Config,
        on_index_complete: Callable | None = None,
    ):
        """Initialize handler.

        Args:
            indexer: Indexer service
            config: Configuration
            on_index_complete: Optional callback when indexing completes
        """
        self.indexer = indexer
        self.config = config
        self.on_index_complete = on_index_complete
        self._pending_files: set[str] = set()
        self._debounce_task: asyncio.Task | None = None

    def _is_code_file(self, path: str) -> bool:
        """Check if path matches code file patterns."""
        path_obj = Path(path)
        for pattern in self.config.file_patterns:
            if path_obj.match(pattern):
                return True
        return False

    def _schedule_index(self, file_path: Path) -> None:
        """Schedule file for indexing with debounce."""
        self._pending_files.add(str(file_path))

        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        self._debounce_task = asyncio.create_task(self._debounce_index())

    async def _debounce_index(self) -> None:
        """Wait for batch of changes then index."""
        try:
            await asyncio.sleep(self.config.debounce_duration)
        except asyncio.CancelledError:
            # Clean cancellation - pending files remain in queue for next batch
            return

        if not self._pending_files:
            return

        files_to_index = list(self._pending_files)
        self._pending_files.clear()

        for file_str in files_to_index:
            file_path = Path(file_str)
            if file_path.exists():
                await self.indexer.index_file(file_path)
            else:
                self.indexer.remove_file(file_path)

        if self.on_index_complete:
            self.on_index_complete(files_to_index)

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
            on_index_complete=on_index_complete,
        )

        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(target_path),
            recursive=True,
        )
        self.observer.start()

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

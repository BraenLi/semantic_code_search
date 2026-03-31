"""Tests for file system watcher service."""

import pytest
import time
from pathlib import Path
from unittest.mock import patch

from semantic_mcp.services.watcher import WatcherService, CodeChangeHandler
from semantic_mcp.services.indexer import Indexer
from semantic_mcp.config import Config, EmbeddingConfig
from watchdog.events import FileCreatedEvent


class TestWatcherService:
    """Test watcher service operations."""

    @pytest.fixture
    def config(self, temp_dir) -> Config:
        """Test configuration."""
        return Config(
            chroma_path=str(Path(temp_dir) / "chroma"),
            target_dir=str(temp_dir),
            embedding=EmbeddingConfig(api_key="test-key"),
            debounce_duration=0.1,  # Short debounce for faster tests
        )

    @pytest.fixture
    def indexer(self, config) -> Indexer:
        """Test indexer."""
        return Indexer(config)

    @pytest.fixture
    def watcher(self, config, indexer) -> WatcherService:
        """Test watcher service."""
        return WatcherService(config=config, indexer=indexer)

    def test_watcher_start_stop_clean(self, watcher, temp_path: Path):
        """Should start and stop watcher cleanly without errors."""
        # Start watcher
        watcher.start()

        # Verify observer is running
        assert watcher.observer is not None
        assert watcher.observer.is_alive()

        # Stop watcher
        watcher.stop()

        # Verify observer is stopped
        assert watcher.observer is None

    def test_watcher_handler_start_stop(self, config, indexer, temp_path: Path):
        """Should start and stop async processor thread cleanly."""
        handler = CodeChangeHandler(indexer=indexer, config=config)

        # Start processor
        handler.start()

        # Verify thread is running
        assert handler._processor_thread is not None
        assert handler._processor_thread.is_alive()

        # Stop processor
        handler.stop()

        # Verify thread is stopped
        assert handler._processor_thread is None

    def test_watcher_handler_timeout_on_stop(self, config, indexer):
        """Should handle stop with timeout gracefully."""
        handler = CodeChangeHandler(indexer=indexer, config=config)
        handler.start()

        # Stop should complete within timeout
        handler.stop()

        # Thread should be None after stop
        assert handler._processor_thread is None

    def test_watcher_file_event_scheduling(self, config, indexer, temp_path: Path):
        """Should schedule file events for processing."""
        handler = CodeChangeHandler(indexer=indexer, config=config)

        # Create test file
        test_file = temp_path / "test_watch.py"
        test_file.write_text("def watched_func(): pass")

        # Start handler
        handler.start()

        try:
            # Trigger handler for the file using proper FileCreatedEvent
            event = FileCreatedEvent(str(test_file))
            handler.on_created(event)

            # Check that file was scheduled (queue should have the file)
            assert not handler._sync_queue.empty()

            # Get the file from queue
            scheduled_file = handler._sync_queue.get_nowait()
            assert scheduled_file == str(test_file)
        finally:
            handler.stop()

    def test_is_code_file_validates_path(self, config, temp_path: Path):
        """Should validate file is under target directory."""
        handler = CodeChangeHandler(indexer=Indexer(config), config=config)

        # Valid file under target directory - create it first
        valid_file = temp_path / "test.py"
        valid_file.write_text("test")
        assert handler._is_code_file(str(valid_file)) is True

        # File outside target directory should be rejected
        # Use a path that's definitely outside target
        outside_path = "/tmp/outside_target.py"
        assert handler._is_code_file(outside_path) is False

    def test_is_code_file_checks_patterns(self, config, temp_path: Path):
        """Should check file matches code patterns."""
        handler = CodeChangeHandler(indexer=Indexer(config), config=config)

        # Python file should match
        py_file = temp_path / "test.py"
        py_file.write_text("test")
        assert handler._is_code_file(str(py_file)) is True

        # Text file should not match
        txt_file = temp_path / "test.txt"
        txt_file.write_text("test")
        assert handler._is_code_file(str(txt_file)) is False

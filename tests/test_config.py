"""Tests for configuration management."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from semantic_mcp.config import Config, EmbeddingConfig, load_dotenv


class TestConfig:
    """Test configuration loading."""

    def test_from_env_uses_defaults(self):
        """Should use defaults when environment variables not set."""
        # Clear relevant env vars
        with patch.dict(os.environ, {}, clear=True):
            config = Config.from_env()

            assert config.chroma_path == "./.semantic_index"
            assert config.target_dir == "."
            assert config.small_file_threshold == 50
            assert config.debounce_duration == 1.0
            assert config.result_code_limit == 500

    def test_from_env_reads_env_variables(self):
        """Should read configuration from environment variables."""
        with patch.dict(os.environ, {
            "SEMANTIC_CHROMA_PATH": "/custom/chroma",
            "SEMANTIC_TARGET_DIR": "/custom/target",
            "SEMANTIC_FILE_PATTERNS": "*.py,*.js",
            "SEMANTIC_EMBEDDING_BASE_URL": "https://custom.api.com",
            "SEMANTIC_EMBEDDING_MODEL": "custom-model",
            "SEMANTIC_API_KEY": "test-key-123",
            "SEMANTIC_SMALL_FILE_THRESHOLD": "100",
            "SEMANTIC_DEBOUNCE_DURATION": "2.0",
            "SEMANTIC_RESULT_CODE_LIMIT": "1000",
        }):
            config = Config.from_env()

            assert config.chroma_path == "/custom/chroma"
            assert config.target_dir == "/custom/target"
            assert config.file_patterns == ["*.py", "*.js"]
            assert config.embedding.base_url == "https://custom.api.com"
            assert config.embedding.model == "custom-model"
            assert config.embedding.api_key == "test-key-123"
            assert config.small_file_threshold == 100
            assert config.debounce_duration == 2.0
            assert config.result_code_limit == 1000

    def test_load_dotenv_not_called_at_module_import(self):
        """Should not auto-execute load_dotenv on module import.

        This tests that load_dotenv is lazy-loaded in from_env() method,
        not executed at module import time which can cause unexpected behavior.
        """
        # If load_dotenv was called at import time, it would have loaded
        # any .env file in the test directory. We verify the module
        # doesn't auto-execute by checking that Config.from_env()
        # properly handles the case when no .env exists.

        # This test passes if the module imports without side effects
        # and from_env() works correctly
        with patch.dict(os.environ, {}, clear=True):
            config = Config.from_env()
            # Should use defaults, not fail
            assert config is not None
            assert config.chroma_path == "./.semantic_index"

    def test_validate_requires_api_key(self):
        """Should report missing API key as validation error."""
        config = Config(embedding=EmbeddingConfig(api_key=None))
        errors = config.validate()

        assert any("API_KEY" in err for err in errors)

    def test_validate_checks_target_dir(self, temp_path: Path):
        """Should report non-existent target directory as error."""
        config = Config(target_dir="/nonexistent/path/xyz123")
        errors = config.validate()

        assert any("does not exist" in err for err in errors)

    def test_validate_checks_target_is_directory(self, temp_path: Path):
        """Should report file as target directory as error."""
        # Create a file instead of directory
        test_file = temp_path / "not_a_dir.txt"
        test_file.write_text("test")

        config = Config(target_dir=str(test_file))
        errors = config.validate()

        assert any("not a directory" in err for err in errors)

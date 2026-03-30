"""Hash utilities for semantic MCP."""

import hashlib


def compute_hash(content: str) -> str:
    """Compute SHA256 hash of content.

    Args:
        content: String content to hash

    Returns:
        First 16 characters of SHA256 hex digest
    """
    return hashlib.sha256(content.encode()).hexdigest()[:16]

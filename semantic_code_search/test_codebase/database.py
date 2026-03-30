"""Database connection and query helpers."""

import sqlite3
from contextlib import contextmanager
from typing import Any, Generator


class DatabaseConnection:
    """Manages database connections and queries."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None
    
    def connect(self) -> sqlite3.Connection:
        """Establish database connection."""
        self._connection = sqlite3.connect(self.db_path)
        return self._connection
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database transactions."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
    
    def get_user(self, username: str) -> Any:
        """Get user by username."""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row
    
    def create_user(self, username: str, password_hash: str, email: str) -> None:
        """Create new user record."""
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                (username, password_hash, email)
            )
    
    def find_user_by_email(self, email: str) -> Any:
        """Find user by email address."""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()

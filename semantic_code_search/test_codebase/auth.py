"""Authentication module for user login and registration."""

import hashlib
from typing import Optional


class UserService:
    """Service for managing user accounts."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._cache = {}
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user with username and password."""
        hashed = hashlib.sha256(password.encode()).hexdigest()
        user = self.db.get_user(username)
        if user and user.password_hash == hashed:
            self._cache[username] = user
            return True
        return False
    
    def register_user(self, username: str, password: str, email: str) -> bool:
        """Register a new user account."""
        if self.db.get_user(username):
            return False
        hashed = hashlib.sha256(password.encode()).hexdigest()
        self.db.create_user(username, hashed, email)
        return True
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Find user by email address."""
        return self.db.find_user_by_email(email)


class SessionManager:
    """Manages user sessions and tokens."""
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, user_id: str) -> str:
        """Create a new session and return session token."""
        import uuid
        token = str(uuid.uuid4())
        self.sessions[token] = user_id
        return token
    
    def validate_session(self, token: str) -> Optional[str]:
        """Validate session token and return user_id if valid."""
        return self.sessions.get(token)
    
    def logout(self, token: str) -> None:
        """End session for given token."""
        self.sessions.pop(token, None)

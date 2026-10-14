"""
Session Manager for managing conversation sessions with in-memory storage.

This module provides the SessionManager class that handles creating, retrieving,
and updating conversation sessions. Sessions are stored in-memory using a dictionary
and include automatic cleanup of expired sessions based on TTL.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional

from .session import Session, ConversationMessage


class SessionManager:
    """Manages conversation sessions with in-memory storage.
    
    The SessionManager is responsible for creating new sessions with unique
    identifiers, retrieving existing sessions, and updating session state.
    Sessions are stored in a dictionary keyed by session_id.
    
    Attributes:
        _sessions: Dictionary mapping session_id to Session objects
        _ttl_minutes: Time-to-live for sessions in minutes (default: 30)
    """
    
    def __init__(self, ttl_minutes: int = 30):
        """Initialize the SessionManager.
        
        Args:
            ttl_minutes: Time-to-live for sessions in minutes (default: 30)
        """
        self._sessions: dict[str, Session] = {}
        self._ttl_minutes = ttl_minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval_seconds = 300  # 5 minutes
    
    def create_session(self) -> str:
        """Create a new session with a unique UUID identifier.
        
        Generates a new UUID4 identifier and creates a Session object
        with that ID. The session is stored in the internal dictionary.
        
        Returns:
            The session_id (UUID string) of the newly created session
        
        Validates: Requirements 5.1
        """
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id)
        self._sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve an existing session by ID.
        
        Looks up the session in the internal dictionary. If found, updates
        the last_accessed timestamp to track session activity.
        
        Args:
            session_id: The UUID string identifying the session
        
        Returns:
            The Session object if found, None otherwise
        
        Validates: Requirements 5.2
        """
        session = self._sessions.get(session_id)
        if session:
            session.last_accessed = datetime.utcnow()
        return session
    
    def update_session(self, session_id: str, message: ConversationMessage) -> bool:
        """Update a session by adding a new message.
        
        Adds the provided message to the session's conversation history.
        Updates the last_accessed timestamp automatically through the
        Session.add_message method.
        
        Args:
            session_id: The UUID string identifying the session
            message: The ConversationMessage to add to the session
        
        Returns:
            True if the session was found and updated, False otherwise
        
        Validates: Requirements 5.2
        """
        session = self._sessions.get(session_id)
        if session:
            session.add_message(message)
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove sessions that have exceeded the TTL.
        
        Iterates through all sessions and removes those that have not been
        accessed within the TTL period (default: 30 minutes). This helps
        manage memory usage by removing stale sessions.
        
        Returns:
            The number of sessions that were removed
        
        Validates: Requirements 5.4
        """
        now = datetime.utcnow()
        ttl_delta = timedelta(minutes=self._ttl_minutes)
        expired_session_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if now - session.last_accessed > ttl_delta
        ]
        
        for session_id in expired_session_ids:
            del self._sessions[session_id]
        
        return len(expired_session_ids)
    
    def get_session_count(self) -> int:
        """Get the current number of active sessions.
        
        Returns:
            The number of sessions currently stored in memory
        """
        return len(self._sessions)
    
    async def _cleanup_loop(self) -> None:
        """Background task that periodically cleans up expired sessions.
        
        Runs every 5 minutes and calls cleanup_expired_sessions to remove
        sessions that have exceeded the TTL. This task runs indefinitely
        until cancelled.
        
        Validates: Requirements 5.4
        """
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval_seconds)
                removed_count = self.cleanup_expired_sessions()
                if removed_count > 0:
                    print(f"Cleaned up {removed_count} expired session(s)")
            except asyncio.CancelledError:
                # Task was cancelled, exit gracefully
                break
            except Exception as e:
                # Log error but continue running
                print(f"Error during session cleanup: {e}")
    
    def start_cleanup_task(self) -> None:
        """Start the background cleanup task.
        
        Creates and schedules an asyncio task that runs the cleanup loop.
        This should be called during application startup.
        
        Validates: Requirements 5.4
        """
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task.
        
        Cancels the running cleanup task if it exists. This should be
        called during application shutdown.
        
        Validates: Requirements 5.4
        """
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

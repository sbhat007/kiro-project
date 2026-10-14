"""
Unit tests for SessionManager class.

Tests the core functionality of session creation, retrieval, updating,
and cleanup of expired sessions.
"""

import pytest
from datetime import datetime, timedelta
from src.session_manager import SessionManager
from src.session import ConversationMessage


def test_create_session_generates_unique_id():
    """Test that create_session generates a unique UUID identifier."""
    manager = SessionManager()
    session_id = manager.create_session()
    
    # Should be a valid UUID string
    assert isinstance(session_id, str)
    assert len(session_id) == 36  # UUID4 format: 8-4-4-4-12
    assert session_id.count('-') == 4


def test_create_session_stores_session():
    """Test that created sessions are stored and retrievable."""
    manager = SessionManager()
    session_id = manager.create_session()
    
    session = manager.get_session(session_id)
    assert session is not None
    assert session.session_id == session_id
    assert len(session.messages) == 0


def test_get_session_returns_none_for_invalid_id():
    """Test that get_session returns None for non-existent session IDs."""
    manager = SessionManager()
    session = manager.get_session("invalid-session-id")
    assert session is None


def test_get_session_updates_last_accessed():
    """Test that retrieving a session updates its last_accessed timestamp."""
    manager = SessionManager()
    session_id = manager.create_session()
    
    session = manager.get_session(session_id)
    first_access = session.last_accessed
    
    # Wait a tiny bit and access again
    import time
    time.sleep(0.01)
    
    session = manager.get_session(session_id)
    second_access = session.last_accessed
    
    assert second_access > first_access


def test_update_session_adds_message():
    """Test that update_session adds a message to the session history."""
    manager = SessionManager()
    session_id = manager.create_session()
    
    message = ConversationMessage(
        role="user",
        content="Hello, chatbot!",
        timestamp=datetime.utcnow()
    )
    
    result = manager.update_session(session_id, message)
    assert result is True
    
    session = manager.get_session(session_id)
    assert len(session.messages) == 1
    assert session.messages[0].content == "Hello, chatbot!"


def test_update_session_returns_false_for_invalid_id():
    """Test that update_session returns False for non-existent sessions."""
    manager = SessionManager()
    message = ConversationMessage(
        role="user",
        content="Hello",
        timestamp=datetime.utcnow()
    )
    
    result = manager.update_session("invalid-id", message)
    assert result is False


def test_cleanup_expired_sessions_removes_old_sessions():
    """Test that cleanup removes sessions older than TTL."""
    manager = SessionManager(ttl_minutes=1)  # 1 minute TTL
    session_id = manager.create_session()
    
    # Manually set last_accessed to 2 minutes ago
    session = manager.get_session(session_id)
    session.last_accessed = datetime.utcnow() - timedelta(minutes=2)
    
    # Cleanup should remove the expired session
    removed_count = manager.cleanup_expired_sessions()
    assert removed_count == 1
    assert manager.get_session(session_id) is None


def test_cleanup_expired_sessions_keeps_active_sessions():
    """Test that cleanup does not remove active sessions."""
    manager = SessionManager(ttl_minutes=30)
    session_id = manager.create_session()
    
    # Session was just created, should not be expired
    removed_count = manager.cleanup_expired_sessions()
    assert removed_count == 0
    assert manager.get_session(session_id) is not None


def test_get_session_count():
    """Test that get_session_count returns the correct number of sessions."""
    manager = SessionManager()
    assert manager.get_session_count() == 0
    
    manager.create_session()
    assert manager.get_session_count() == 1
    
    manager.create_session()
    assert manager.get_session_count() == 2


def test_multiple_sessions_are_independent():
    """Test that multiple sessions maintain independent state."""
    manager = SessionManager()
    session_id_1 = manager.create_session()
    session_id_2 = manager.create_session()
    
    message_1 = ConversationMessage(
        role="user",
        content="Message for session 1",
        timestamp=datetime.utcnow()
    )
    message_2 = ConversationMessage(
        role="user",
        content="Message for session 2",
        timestamp=datetime.utcnow()
    )
    
    manager.update_session(session_id_1, message_1)
    manager.update_session(session_id_2, message_2)
    
    session_1 = manager.get_session(session_id_1)
    session_2 = manager.get_session(session_id_2)
    
    assert len(session_1.messages) == 1
    assert len(session_2.messages) == 1
    assert session_1.messages[0].content == "Message for session 1"
    assert session_2.messages[0].content == "Message for session 2"

"""
Unit tests for SessionManager background cleanup task.

Tests the background task functionality that periodically cleans up
expired sessions every 5 minutes.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.session_manager import SessionManager
from src.session import ConversationMessage


@pytest.mark.asyncio
async def test_start_cleanup_task_creates_task():
    """Test that start_cleanup_task creates an asyncio task."""
    manager = SessionManager()
    manager.start_cleanup_task()
    
    assert manager._cleanup_task is not None
    assert isinstance(manager._cleanup_task, asyncio.Task)
    assert not manager._cleanup_task.done()
    
    # Cleanup
    manager.stop_cleanup_task()
    await asyncio.sleep(0.01)  # Allow task to cancel


@pytest.mark.asyncio
async def test_stop_cleanup_task_cancels_task():
    """Test that stop_cleanup_task cancels the running task."""
    manager = SessionManager()
    manager.start_cleanup_task()
    
    assert not manager._cleanup_task.done()
    
    manager.stop_cleanup_task()
    await asyncio.sleep(0.01)  # Allow task to cancel
    
    assert manager._cleanup_task.cancelled() or manager._cleanup_task.done()


@pytest.mark.asyncio
async def test_cleanup_task_removes_expired_sessions():
    """Test that the background task actually cleans up expired sessions."""
    # Use very short intervals for testing
    manager = SessionManager(ttl_minutes=0)  # Expire immediately
    manager._cleanup_interval_seconds = 0.1  # Run every 100ms
    
    # Create a session
    session_id = manager.create_session()
    assert manager.get_session_count() == 1
    
    # Manually expire the session
    session = manager.get_session(session_id)
    session.last_accessed = datetime.utcnow() - timedelta(minutes=1)
    
    # Start the cleanup task
    manager.start_cleanup_task()
    
    # Wait for cleanup to run (slightly longer than interval)
    await asyncio.sleep(0.2)
    
    # Session should be cleaned up
    assert manager.get_session_count() == 0
    
    # Cleanup
    manager.stop_cleanup_task()
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_cleanup_task_keeps_active_sessions():
    """Test that the background task does not remove active sessions."""
    manager = SessionManager(ttl_minutes=30)
    manager._cleanup_interval_seconds = 0.1  # Run every 100ms
    
    # Create a session
    session_id = manager.create_session()
    assert manager.get_session_count() == 1
    
    # Start the cleanup task
    manager.start_cleanup_task()
    
    # Wait for cleanup to run
    await asyncio.sleep(0.2)
    
    # Session should still exist
    assert manager.get_session_count() == 1
    assert manager.get_session(session_id) is not None
    
    # Cleanup
    manager.stop_cleanup_task()
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_start_cleanup_task_is_idempotent():
    """Test that calling start_cleanup_task multiple times doesn't create multiple tasks."""
    manager = SessionManager()
    
    manager.start_cleanup_task()
    first_task = manager._cleanup_task
    
    manager.start_cleanup_task()
    second_task = manager._cleanup_task
    
    # Should be the same task
    assert first_task is second_task
    
    # Cleanup
    manager.stop_cleanup_task()
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_cleanup_task_handles_errors_gracefully():
    """Test that errors in cleanup don't crash the background task."""
    manager = SessionManager()
    manager._cleanup_interval_seconds = 0.05  # Run every 50ms
    
    # Start the task
    manager.start_cleanup_task()
    
    # Simulate an error by corrupting internal state temporarily
    original_sessions = manager._sessions
    manager._sessions = None  # This will cause an error in cleanup
    
    # Wait for cleanup to run (it should handle the error)
    await asyncio.sleep(0.1)
    
    # Task should still be running despite the error
    assert not manager._cleanup_task.done()
    
    # Restore state
    manager._sessions = original_sessions
    
    # Cleanup
    manager.stop_cleanup_task()
    await asyncio.sleep(0.01)

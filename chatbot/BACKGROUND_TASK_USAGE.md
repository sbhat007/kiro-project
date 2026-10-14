# Background Task Usage

This document explains how to use the SessionManager's background cleanup task in the FastAPI application.

## Overview

The SessionManager includes a background task that automatically cleans up expired sessions every 5 minutes. This helps manage memory usage by removing sessions that haven't been accessed within the TTL period (default: 30 minutes).

## Implementation

The background task is implemented using asyncio and includes three key methods:

1. `start_cleanup_task()` - Starts the background cleanup task
2. `stop_cleanup_task()` - Stops the background cleanup task
3. `_cleanup_loop()` - Internal method that runs the cleanup loop

## Usage in FastAPI Application

When creating the FastAPI application (in `main.py`), you should start the background task during application startup and stop it during shutdown:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.session_manager import SessionManager

# Create session manager instance
session_manager = SessionManager(ttl_minutes=30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background cleanup task
    session_manager.start_cleanup_task()
    print("Background session cleanup task started")
    
    yield
    
    # Shutdown: Stop the background cleanup task
    session_manager.stop_cleanup_task()
    print("Background session cleanup task stopped")

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Your API endpoints here...
```

## Alternative: Using Startup/Shutdown Events (Deprecated in FastAPI 0.109+)

If using an older version of FastAPI, you can use startup and shutdown events:

```python
from fastapi import FastAPI
from src.session_manager import SessionManager

app = FastAPI()
session_manager = SessionManager(ttl_minutes=30)

@app.on_event("startup")
async def startup_event():
    session_manager.start_cleanup_task()
    print("Background session cleanup task started")

@app.on_event("shutdown")
async def shutdown_event():
    session_manager.stop_cleanup_task()
    print("Background session cleanup task stopped")
```

## Configuration

The cleanup behavior can be configured through the SessionManager constructor:

- `ttl_minutes`: Time-to-live for sessions in minutes (default: 30)
- `_cleanup_interval_seconds`: How often cleanup runs (default: 300 seconds / 5 minutes)

Example with custom configuration:

```python
# Sessions expire after 60 minutes
session_manager = SessionManager(ttl_minutes=60)

# To change cleanup interval (for testing or special cases)
session_manager._cleanup_interval_seconds = 600  # Run every 10 minutes
```

## Testing

The background task functionality is fully tested in `tests/unit/test_session_manager_background.py`. Tests verify:

- Task creation and cancellation
- Actual cleanup of expired sessions
- Preservation of active sessions
- Error handling
- Idempotency of start_cleanup_task()

## How It Works

1. When `start_cleanup_task()` is called, it creates an asyncio task that runs `_cleanup_loop()`
2. The loop sleeps for 5 minutes, then calls `cleanup_expired_sessions()`
3. If any sessions are removed, it logs the count
4. The loop continues indefinitely until the task is cancelled
5. When `stop_cleanup_task()` is called, it cancels the running task
6. The loop catches `asyncio.CancelledError` and exits gracefully

## Error Handling

The background task includes error handling to ensure it continues running even if cleanup encounters an error:

- `asyncio.CancelledError`: Caught and handled gracefully during shutdown
- Other exceptions: Logged but don't stop the background task from continuing

This ensures the cleanup task remains resilient and doesn't crash the application.

## Validates

This implementation validates **Requirements 5.4**: Session cleanup and TTL management.

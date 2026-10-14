"""
Basic test to verify ChatHandler implementation.

This test checks that the ChatHandler can be instantiated and that
the basic structure is correct.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_settings
from src.backend_client import BackendClient
from src.tools import ToolRegistry
from src.session import Session
from src.chat_handler import ChatHandler


async def test_chat_handler_initialization():
    """Test that ChatHandler can be initialized."""
    print("Testing ChatHandler initialization...")
    
    # Create dependencies
    settings = get_settings()
    backend_client = BackendClient(
        base_url=settings.backend_base_url,
        timeout=settings.backend_timeout
    )
    tool_registry = ToolRegistry(backend_client)
    
    # Initialize ChatHandler
    try:
        chat_handler = ChatHandler(tool_registry)
        print("✓ ChatHandler initialized successfully")
        print(f"  - Model ID: {chat_handler.settings.bedrock_model_id}")
        print(f"  - Temperature: {chat_handler.settings.llm_temperature}")
        print(f"  - Max tokens: {chat_handler.settings.llm_max_tokens}")
        print(f"  - Tools available: {len(tool_registry.list_tools())}")
        return True
    except Exception as e:
        print(f"✗ ChatHandler initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_build_context():
    """Test the _build_context method."""
    print("\nTesting _build_context method...")
    
    try:
        # Create dependencies
        settings = get_settings()
        backend_client = BackendClient(
            base_url=settings.backend_base_url,
            timeout=settings.backend_timeout
        )
        tool_registry = ToolRegistry(backend_client)
        chat_handler = ChatHandler(tool_registry)
        
        # Create a test session with some messages
        from datetime import datetime
        from src.session import ConversationMessage
        
        session = Session(session_id="test-session-123")
        session.add_message(ConversationMessage(
            role="user",
            content="Hello",
            timestamp=datetime.utcnow()
        ))
        session.add_message(ConversationMessage(
            role="assistant",
            content="Hi! How can I help you?",
            timestamp=datetime.utcnow()
        ))
        
        # Build context
        context = chat_handler._build_context(session)
        
        print(f"✓ Context built successfully")
        print(f"  - Messages in context: {len(context)}")
        print(f"  - First message role: {context[0]['role']}")
        print(f"  - First message content: {context[0]['content'][:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ _build_context failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ChatHandler Basic Tests")
    print("=" * 60)
    
    results = []
    
    # Test initialization
    results.append(await test_chat_handler_initialization())
    
    # Test build context
    results.append(await test_build_context())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

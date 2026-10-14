"""
Unit tests for ChatHandler.

Tests the ChatHandler class implementation including:
- Initialization with Strands SDK
- Message processing flow
- Context building
- Tool call execution
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.chat_handler import ChatHandler
from src.tools import ToolRegistry
from src.session import Session, ConversationMessage
from src.backend_client import BackendClient


@pytest.fixture
def mock_backend_client():
    """Create a mock backend client."""
    client = Mock(spec=BackendClient)
    client.get_products = AsyncMock(return_value=[])
    client.get_product_details = AsyncMock(return_value={})
    client.get_cart = AsyncMock(return_value=[])
    client.add_to_cart = AsyncMock(return_value={})
    client.update_cart_item = AsyncMock(return_value={})
    client.remove_cart_item = AsyncMock(return_value={})
    return client


@pytest.fixture
def tool_registry(mock_backend_client):
    """Create a tool registry with mock backend client."""
    return ToolRegistry(mock_backend_client)


@pytest.fixture
def test_session():
    """Create a test session with some message history."""
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
    return session


class TestChatHandlerInitialization:
    """Tests for ChatHandler initialization."""
    
    def test_initialization_creates_model(self, tool_registry):
        """Test that initialization creates a BedrockModel instance."""
        with patch('src.chat_handler.BedrockModel') as mock_model_class:
            with patch('src.chat_handler.Agent') as mock_agent_class:
                chat_handler = ChatHandler(tool_registry)
                
                # Verify BedrockModel was created with correct parameters
                mock_model_class.assert_called_once()
                call_kwargs = mock_model_class.call_args[1]
                
                assert call_kwargs['model_id'] == 'amazon.nova-pro-v1:0'
                assert call_kwargs['temperature'] == 0.7
                assert call_kwargs['max_tokens'] == 2048
                assert call_kwargs['streaming'] == False
    
    def test_initialization_creates_agent(self, tool_registry):
        """Test that initialization creates a Strands Agent instance."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent') as mock_agent_class:
                chat_handler = ChatHandler(tool_registry)
                
                # Verify Agent was created
                mock_agent_class.assert_called_once()
                call_kwargs = mock_agent_class.call_args[1]
                
                # Verify system prompt is set
                assert 'system_prompt' in call_kwargs
                assert 'shopping assistant' in call_kwargs['system_prompt'].lower()
    
    def test_initialization_registers_tools(self, tool_registry):
        """Test that initialization registers all tools with the agent."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent') as mock_agent_class:
                chat_handler = ChatHandler(tool_registry)
                
                # Verify tools were passed to Agent
                call_kwargs = mock_agent_class.call_args[1]
                assert 'tools' in call_kwargs
                
                # Should have 3 tools: browse_products, manage_cart, get_recommendations
                tools = call_kwargs['tools']
                assert len(tools) == 3


class TestContextBuilding:
    """Tests for conversation context building."""
    
    def test_build_context_converts_messages(self, tool_registry, test_session):
        """Test that _build_context converts session messages to Strands format."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent'):
                chat_handler = ChatHandler(tool_registry)
                
                context = chat_handler._build_context(test_session)
                
                # Should have 2 messages from test_session
                assert len(context) == 2
                
                # Check format
                assert context[0]['role'] == 'user'
                assert context[0]['content'] == 'Hello'
                assert context[1]['role'] == 'assistant'
                assert context[1]['content'] == 'Hi! How can I help you?'
    
    def test_build_context_limits_messages(self, tool_registry):
        """Test that _build_context limits context to max_context_messages."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent'):
                chat_handler = ChatHandler(tool_registry)
                
                # Create session with many messages
                session = Session(session_id="test-session")
                for i in range(30):
                    session.add_message(ConversationMessage(
                        role="user" if i % 2 == 0 else "assistant",
                        content=f"Message {i}",
                        timestamp=datetime.utcnow()
                    ))
                
                context = chat_handler._build_context(session)
                
                # Should be limited to max_context_messages (20 by default)
                assert len(context) <= chat_handler.settings.max_context_messages
    
    def test_build_context_empty_session(self, tool_registry):
        """Test that _build_context handles empty session."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent'):
                chat_handler = ChatHandler(tool_registry)
                
                session = Session(session_id="empty-session")
                context = chat_handler._build_context(session)
                
                assert len(context) == 0


class TestMessageProcessing:
    """Tests for message processing."""
    
    @pytest.mark.asyncio
    async def test_process_message_adds_user_message(self, tool_registry, test_session):
        """Test that process_message adds user message to session."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent') as mock_agent_class:
                # Mock agent response
                mock_agent = MagicMock()
                mock_response = MagicMock()
                mock_response.message = "I can help you with that!"
                mock_agent.invoke_async = AsyncMock(return_value=mock_response)
                mock_agent_class.return_value = mock_agent
                
                chat_handler = ChatHandler(tool_registry)
                
                initial_message_count = len(test_session.messages)
                
                await chat_handler.process_message("Show me products", test_session)
                
                # Should have added 2 messages (user + assistant)
                assert len(test_session.messages) == initial_message_count + 2
                
                # Check user message was added
                user_msg = test_session.messages[-2]
                assert user_msg.role == "user"
                assert user_msg.content == "Show me products"
    
    @pytest.mark.asyncio
    async def test_process_message_adds_assistant_response(self, tool_registry, test_session):
        """Test that process_message adds assistant response to session."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent') as mock_agent_class:
                # Mock agent response
                mock_agent = MagicMock()
                mock_response = MagicMock()
                mock_response.message = "Here are the products!"
                mock_agent.invoke_async = AsyncMock(return_value=mock_response)
                mock_agent_class.return_value = mock_agent
                
                chat_handler = ChatHandler(tool_registry)
                
                response = await chat_handler.process_message("Show me products", test_session)
                
                # Check assistant message was added
                assistant_msg = test_session.messages[-1]
                assert assistant_msg.role == "assistant"
                assert assistant_msg.content == "Here are the products!"
                
                # Check return value
                assert response == "Here are the products!"
    
    @pytest.mark.asyncio
    async def test_process_message_invokes_agent(self, tool_registry, test_session):
        """Test that process_message invokes the Strands agent."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent') as mock_agent_class:
                # Mock agent
                mock_agent = MagicMock()
                mock_response = MagicMock()
                mock_response.message = "Response"
                mock_agent.invoke_async = AsyncMock(return_value=mock_response)
                mock_agent_class.return_value = mock_agent
                
                chat_handler = ChatHandler(tool_registry)
                
                await chat_handler.process_message("Test message", test_session)
                
                # Verify agent was invoked
                mock_agent.invoke_async.assert_called_once_with("Test message")
    
    @pytest.mark.asyncio
    async def test_process_message_updates_agent_context(self, tool_registry, test_session):
        """Test that process_message updates agent with conversation history."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent') as mock_agent_class:
                # Mock agent
                mock_agent = MagicMock()
                mock_response = MagicMock()
                mock_response.message = "Response"
                mock_agent.invoke_async = AsyncMock(return_value=mock_response)
                mock_agent_class.return_value = mock_agent
                
                chat_handler = ChatHandler(tool_registry)
                
                await chat_handler.process_message("Test message", test_session)
                
                # Verify agent.messages was set with context
                assert hasattr(mock_agent, 'messages')
                assert len(mock_agent.messages) > 0


class TestToolCallExecution:
    """Tests for tool call execution."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_processes_all_calls(self, tool_registry):
        """Test that _execute_tool_calls processes all tool calls."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent'):
                chat_handler = ChatHandler(tool_registry)
                
                tool_calls = [
                    {
                        "id": "call-1",
                        "name": "browse_products",
                        "input": {}
                    },
                    {
                        "id": "call-2",
                        "name": "manage_cart",
                        "input": {"action": "view"}
                    }
                ]
                
                results = await chat_handler._execute_tool_calls(tool_calls)
                
                # Should have 2 results
                assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_handles_errors(self, tool_registry):
        """Test that _execute_tool_calls handles tool execution errors gracefully."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent'):
                chat_handler = ChatHandler(tool_registry)
                
                # Mock tool registry to raise error
                with patch.object(tool_registry, 'execute_tool', side_effect=Exception("Tool error")):
                    tool_calls = [
                        {
                            "id": "call-1",
                            "name": "browse_products",
                            "input": {}
                        }
                    ]
                    
                    results = await chat_handler._execute_tool_calls(tool_calls)
                    
                    # Should still return a result with error status
                    assert len(results) == 1
                    assert results[0]['status'] == 'error'
                    assert 'error' in results[0]['content'][0]['text'].lower()
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_formats_results(self, tool_registry):
        """Test that _execute_tool_calls formats results correctly for LLM."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent'):
                chat_handler = ChatHandler(tool_registry)
                
                tool_calls = [
                    {
                        "id": "call-1",
                        "name": "browse_products",
                        "input": {}
                    }
                ]
                
                results = await chat_handler._execute_tool_calls(tool_calls)
                
                # Check result format
                assert 'toolUseId' in results[0]
                assert results[0]['toolUseId'] == 'call-1'
                assert 'status' in results[0]
                assert 'content' in results[0]


class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_process_message_propagates_exceptions(self, tool_registry, test_session):
        """Test that process_message propagates exceptions from agent."""
        with patch('src.chat_handler.BedrockModel'):
            with patch('src.chat_handler.Agent') as mock_agent_class:
                # Mock agent to raise exception
                mock_agent = MagicMock()
                mock_agent.invoke_async = AsyncMock(side_effect=Exception("LLM error"))
                mock_agent_class.return_value = mock_agent
                
                chat_handler = ChatHandler(tool_registry)
                
                with pytest.raises(Exception) as exc_info:
                    await chat_handler.process_message("Test", test_session)
                
                assert "LLM error" in str(exc_info.value)

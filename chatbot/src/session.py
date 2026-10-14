"""
Internal data models for session management and conversation tracking.

This module defines dataclasses for managing conversation sessions, messages,
tool calls, and tool results. These models are used internally by the chatbot
service and are not exposed directly through the API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class ToolCall:
    """Represents a tool invocation request from the LLM.
    
    Attributes:
        tool_name: Name of the tool to execute
        parameters: Dictionary of parameters to pass to the tool
        call_id: Unique identifier for this tool call
    """
    tool_name: str
    parameters: dict
    call_id: str


@dataclass
class ToolResult:
    """Represents the result of a tool execution.
    
    Attributes:
        call_id: Unique identifier matching the ToolCall
        result: Dictionary containing the tool execution result
        error: Optional error message if tool execution failed
    """
    call_id: str
    result: dict
    error: str | None = None


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation.
    
    Attributes:
        role: Message role (user, assistant, or system)
        content: Text content of the message
        timestamp: When the message was created
        tool_calls: Optional list of tool calls made by the assistant
        tool_results: Optional list of tool execution results
    """
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    tool_calls: list[dict] | None = None
    tool_results: list[dict] | None = None


@dataclass
class Session:
    """Represents a conversation session with message history.
    
    A session maintains the conversation context for a user, including all
    messages exchanged and metadata about the session lifecycle.
    
    Attributes:
        session_id: Unique identifier for this session (UUID)
        messages: List of conversation messages in chronological order
        created_at: When the session was created
        last_accessed: When the session was last used
        metadata: Additional session data (user preferences, etc.)
    """
    session_id: str
    messages: list[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)
    
    def add_message(self, message: ConversationMessage) -> None:
        """Add a message to the conversation history.
        
        Updates the last_accessed timestamp to track session activity.
        
        Args:
            message: The conversation message to add
        """
        self.messages.append(message)
        self.last_accessed = datetime.utcnow()
    
    def get_context_window(self, max_messages: int = 20) -> list[ConversationMessage]:
        """Get recent messages for LLM context.
        
        Returns the most recent messages up to the specified limit to prevent
        token overflow in LLM requests. This implements a sliding window over
        the conversation history.
        
        Args:
            max_messages: Maximum number of recent messages to return (default: 20)
        
        Returns:
            List of recent conversation messages, oldest first
        """
        return self.messages[-max_messages:]

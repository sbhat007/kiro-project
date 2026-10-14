"""
Chat handler for orchestrating LLM interactions via Strands SDK.

This module provides the ChatHandler class that manages communication with
AWS Bedrock Nova Pro through the Strands SDK, including conversation context
building, tool execution, and response generation.
"""

import logging
from typing import Optional
from datetime import datetime

from strands.models import BedrockModel
from strands import Agent

from .session import Session, ConversationMessage
from .tools import ToolRegistry
from .config import get_settings

logger = logging.getLogger(__name__)


class ChatHandler:
    """
    Orchestrates LLM interactions via Strands SDK.
    
    The ChatHandler manages the complete flow of processing user messages:
    1. Building conversation context from session history
    2. Sending requests to Bedrock Nova Pro with available tools
    3. Executing tool calls if the model requests them
    4. Generating and returning the final assistant response
    
    Attributes:
        model: BedrockModel instance configured for Nova Pro
        agent: Strands Agent instance for LLM interactions
        tool_registry: Registry of available tools for function calling
        settings: Application settings
    """
    
    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize the ChatHandler with Strands SDK integration.
        
        Args:
            tool_registry: Registry containing all available tools
        """
        self.settings = get_settings()
        self.tool_registry = tool_registry
        
        # Initialize Bedrock model with Nova Pro configuration
        logger.info(
            f"Initializing BedrockModel with model_id={self.settings.bedrock_model_id}, "
            f"region={self.settings.aws_region}, temperature={self.settings.llm_temperature}"
        )
        
        self.model = BedrockModel(
            model_id=self.settings.bedrock_model_id,
            region_name=self.settings.aws_region,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            streaming=False  # Nova Pro requires non-streaming mode for tool use
        )
        
        # Create system prompt for chatbot behavior
        system_prompt = """You are a helpful shopping assistant for an e-commerce store. 
Your role is to help users browse products, manage their shopping cart, and get personalized recommendations.

You have access to the following capabilities:
- Browse products and view product details including reviews
- Manage shopping cart (view, add, update, remove items)
- Provide personalized product recommendations based on category and price range

Be friendly, concise, and helpful. When users ask about products, use the available tools to fetch real-time information.
Always confirm actions like adding items to the cart and provide clear feedback about what was done."""
        
        # Initialize Strands Agent with model and tools
        logger.info(f"Initializing Strands Agent with {len(self.tool_registry.list_tools())} tools")
        
        self.agent = Agent(
            model=self.model,
            tools=self._get_strands_tools(),
            system_prompt=system_prompt
        )
        
        logger.info("ChatHandler initialized successfully")
    
    def _get_strands_tools(self) -> list:
        """
        Convert tool registry tools to Strands-compatible format.
        
        The Strands SDK expects tools to be Python functions decorated with @tool.
        Since our tools are class-based, we create wrapper functions that delegate
        to the ToolRegistry for execution.
        
        Returns:
            List of tool functions compatible with Strands SDK
        """
        from strands import tool as strands_tool
        
        strands_tools = []
        
        # Get all tool definitions from registry
        for tool_def in self.tool_registry.get_all_tool_definitions():
            tool_name = tool_def["name"]
            tool_description = tool_def["description"]
            tool_params = tool_def["parameters"]
            
            # Create a wrapper function with proper closure using a factory
            def make_tool_wrapper(name: str, desc: str, params: dict):
                """Factory function to create tool wrapper with correct closure."""
                
                # Create the actual wrapper function
                async def tool_func(**kwargs):
                    """Execute tool via registry."""
                    result = await self.tool_registry.execute_tool(name, **kwargs)
                    return result
                
                # Apply the Strands tool decorator
                decorated_tool = strands_tool(
                    name=name,
                    description=desc,
                    inputSchema=params
                )(tool_func)
                
                return decorated_tool
            
            # Create and add the wrapped tool
            wrapped_tool = make_tool_wrapper(tool_name, tool_description, tool_params)
            strands_tools.append(wrapped_tool)
        
        logger.debug(f"Created {len(strands_tools)} Strands-compatible tools")
        
        return strands_tools
    
    async def process_message(self, message: str, session: Session) -> str:
        """
        Process a user message and return the assistant's response.
        
        This method orchestrates the complete message processing flow:
        1. Build conversation context from session history
        2. Send request to Bedrock Nova Pro with tools
        3. Handle tool calls if present
        4. Return the final assistant response
        
        Args:
            message: The user's message text
            session: The conversation session containing history
            
        Returns:
            The assistant's response text
            
        Raises:
            Exception: If LLM invocation or tool execution fails
        """
        logger.info(f"Processing message for session {session.session_id}")
        
        try:
            # Build conversation context from session history
            context_messages = self._build_context(session)
            
            # Add the new user message to context
            user_message = ConversationMessage(
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            session.add_message(user_message)
            
            logger.debug(f"Built context with {len(context_messages)} historical messages")
            
            # Update agent with conversation history
            if context_messages:
                self.agent.messages = context_messages
            
            # Invoke the agent with the user's message
            logger.info("Invoking Strands Agent")
            response = await self.agent.invoke_async(message)
            
            # Extract the assistant's response text
            assistant_response = response.message
            
            logger.info(f"Received response from agent: {len(assistant_response)} characters")
            
            # Add assistant response to session
            assistant_message = ConversationMessage(
                role="assistant",
                content=assistant_response,
                timestamp=datetime.utcnow()
            )
            session.add_message(assistant_message)
            
            return assistant_response
            
        except Exception as e:
            logger.error(f"Error processing message: {type(e).__name__} - {str(e)}")
            raise
    
    def _build_context(self, session: Session) -> list[dict]:
        """
        Convert session messages to Strands-compatible format.
        
        This method takes the session's message history and converts it to the
        format expected by the Strands SDK, limiting the context to the most
        recent messages to prevent token overflow.
        
        Args:
            session: The conversation session
            
        Returns:
            List of message dictionaries in Strands format
        """
        # Get recent messages within the context window
        recent_messages = session.get_context_window(
            max_messages=self.settings.max_context_messages
        )
        
        # Convert to Strands message format
        strands_messages = []
        for msg in recent_messages:
            strands_message = {
                "role": msg.role,
                "content": msg.content
            }
            strands_messages.append(strands_message)
        
        logger.debug(f"Built context with {len(strands_messages)} messages")
        
        return strands_messages
    
    async def _execute_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        """
        Execute tool calls and collect results.
        
        This method processes tool call requests from the LLM, executes each
        tool via the ToolRegistry, and formats the results for the LLM.
        
        Args:
            tool_calls: List of tool call dictionaries from the LLM
            
        Returns:
            List of tool result dictionaries formatted for the LLM
        """
        logger.info(f"Executing {len(tool_calls)} tool calls")
        
        tool_results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_params = tool_call.get("input", {})
            call_id = tool_call.get("id")
            
            logger.info(f"Executing tool: {tool_name} with params: {tool_params}")
            
            try:
                # Execute the tool via registry
                result = await self.tool_registry.execute_tool(tool_name, **tool_params)
                
                # Format result for LLM
                tool_result = {
                    "toolUseId": call_id,
                    "status": "success" if result.get("success", True) else "error",
                    "content": [{"json": result}]
                }
                
                logger.info(f"Tool {tool_name} executed successfully")
                
            except Exception as e:
                # Handle tool execution errors gracefully
                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                
                tool_result = {
                    "toolUseId": call_id,
                    "status": "error",
                    "content": [{
                        "text": f"Error executing {tool_name}: {str(e)}"
                    }]
                }
            
            tool_results.append(tool_result)
        
        logger.info(f"Completed execution of {len(tool_results)} tool calls")
        
        return tool_results

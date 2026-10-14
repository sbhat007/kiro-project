# Implementation Plan: Shopping Assistant Chatbot

## Overview

This implementation plan breaks down the Shopping Assistant Chatbot feature into discrete coding tasks. The chatbot is a Python-based HTTP service that integrates AWS Bedrock Nova Pro via the Strands SDK to provide natural language interaction with the existing e-commerce backend. The implementation follows a bottom-up approach, building core components first, then integrating them, and finally adding the HTTP interface.

## Tasks

- [x] 1. Set up project structure and environment
  - Create `chatbot/` directory at project root
  - Set up Python virtual environment with Python 3.11+
  - Create `requirements.txt` with dependencies: fastapi, uvicorn, pydantic, pydantic-settings, strands-sdk, httpx, python-dotenv, hypothesis, pytest, pytest-asyncio
  - Create `.env.example` file with required environment variables
  - Create project structure: `src/`, `tests/unit/`, `tests/integration/`, `tests/property/`
  - Create `__init__.py` files for Python packages
  - _Requirements: 8.1, 8.2_

- [x] 2. Implement configuration management
  - [x] 2.1 Create configuration models using Pydantic Settings
    - Implement `Settings` class with AWS, server, backend, session, and LLM configuration
    - Add environment variable loading with `.env` file support
    - Include validation for required fields and sensible defaults
    - _Requirements: 8.1, 8.2_


  - [ ]* 2.2 Write unit tests for configuration loading
    - Test environment variable loading
    - Test default values
    - Test validation errors for missing required fields
    - _Requirements: 8.1_

- [x] 3. Implement data models
  - [x] 3.1 Create Pydantic models for API requests and responses
    - Implement `ChatRequest`, `ChatResponse`, `ErrorResponse`, `HealthResponse` models
    - Add field validation (message length, session_id format)
    - _Requirements: 2.2, 10.1_

  - [x] 3.2 Create internal data models
    - Implement `ConversationMessage`, `Session`, `ToolCall`, `ToolResult` dataclasses
    - Add helper methods for session management (add_message, get_context_window)
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 3.3 Write unit tests for data models
    - Test model validation and serialization
    - Test session helper methods
    - Test context window limiting
    - _Requirements: 5.2, 5.3_

- [ ] 4. Implement Backend Integration Client
  - [x] 4.1 Create BackendClient class with async HTTP methods
    - Implement methods: get_products, get_product_details, get_cart, add_to_cart, update_cart_item, remove_cart_item
    - Add timeout configuration (10 seconds)
    - Use httpx for async HTTP requests
    - _Requirements: 3.1, 4.1, 7.1_

  - [x] 4.2 Add retry logic with exponential backoff
    - Implement retry decorator for connection errors and timeouts
    - Configure 3 retry attempts with 1.5x backoff multiplier
    - _Requirements: 7.3_

  - [x] 4.3 Add error handling for backend responses
    - Handle connection errors, timeouts, 404, 500 errors
    - Return structured error responses
    - _Requirements: 7.2, 7.3_

  - [ ]* 4.4 Write unit tests for BackendClient
    - Mock HTTP responses for all methods
    - Test retry logic with simulated failures
    - Test error handling for various HTTP status codes
    - _Requirements: 7.2, 7.3_

  - [ ]* 4.5 Write property test for backend timeout retry logic
    - **Property 14: Backend timeouts trigger retry logic**
    - **Validates: Requirements 7.3**

- [x] 5. Implement Tool Registry and Tools
  - [x] 5.1 Create abstract Tool base class
    - Define abstract methods: execute, get_definition
    - _Requirements: 6.1_

  - [x] 5.2 Implement ProductBrowserTool
    - Handle product listing (no product_id) and product details (with product_id)
    - Call BackendClient methods appropriately
    - Return formatted results for LLM consumption
    - _Requirements: 3.2, 3.3_

  - [ ]* 5.3 Write property tests for ProductBrowserTool
    - **Property 3: Product browsing tool calls correct backend endpoint**
    - **Property 4: Product details tool calls correct backend endpoint**
    - **Validates: Requirements 3.2, 3.3**

  - [x] 5.4 Implement CartManagerTool
    - Handle actions: view, add, update, remove
    - Call appropriate BackendClient methods based on action
    - Validate required parameters for each action
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.5 Write property tests for CartManagerTool
    - **Property 5: Cart view tool calls correct backend endpoint**
    - **Property 6: Cart add tool calls correct backend endpoint**
    - **Property 7: Cart update tool calls correct backend endpoint**
    - **Property 8: Cart remove tool calls correct backend endpoint**
    - **Validates: Requirements 4.2, 4.3, 4.4, 4.5**

  - [x] 5.6 Implement RecommendationTool
    - Fetch products from backend
    - Apply category filtering based on name/description matching
    - Apply price range filtering (min/max inclusive)
    - Apply result limit
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ]* 5.7 Write property tests for RecommendationTool filtering
    - **Property 16: Recommendations tool fetches from backend**
    - **Property 17: Price range filtering is applied correctly**
    - **Property 18: Category filtering is applied correctly**
    - **Property 19: Result limit is respected**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

  - [x] 5.8 Create ToolRegistry class
    - Register all tools with their definitions
    - Provide method to get tool by name
    - Provide method to get all tool definitions for LLM
    - _Requirements: 6.1_

  - [ ]* 5.9 Write unit tests for ToolRegistry
    - Test tool registration and retrieval
    - Test tool definition formatting
    - _Requirements: 6.1_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 7. Implement Session Manager
  - [x] 7.1 Create SessionManager class with in-memory storage
    - Implement create_session method (generate UUID4)
    - Implement get_session method
    - Implement update_session method
    - Use dictionary for session storage
    - _Requirements: 5.1, 5.2_

  - [x] 7.2 Add session cleanup logic
    - Implement cleanup_expired_sessions method
    - Remove sessions older than TTL (30 minutes)
    - _Requirements: 5.4_

  - [x] 7.3 Add background task for periodic cleanup
    - Schedule cleanup every 5 minutes
    - Use asyncio background task
    - _Requirements: 5.4_

  - [ ]* 7.4 Write unit tests for SessionManager
    - Test session creation with unique IDs
    - Test session retrieval
    - Test session updates
    - Test TTL expiration logic
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 7.5 Write property tests for session management
    - **Property 2: Session context is maintained across requests**
    - **Property 9: New sessions are created for requests without session_id**
    - **Property 10: Conversation history is updated after each exchange**
    - **Property 11: Expired sessions are cleaned up**
    - **Validates: Requirements 2.4, 5.1, 5.2, 5.3, 5.4**

- [x] 8. Implement Chat Handler
  - [x] 8.1 Create ChatHandler class with Strands SDK integration
    - Initialize Strands client with AWS credentials
    - Configure model: amazon.nova-pro-v1:0
    - Set temperature: 0.7, max_tokens: 2048
    - _Requirements: 1.1, 1.2, 6.1_

  - [x] 8.2 Implement process_message method
    - Build conversation context from session history
    - Send request to Bedrock Nova Pro with tools
    - Handle tool calls if present
    - Return assistant response
    - _Requirements: 2.3, 6.2, 6.3_

  - [x] 8.3 Implement _build_context helper method
    - Convert session messages to Strands format
    - Limit context to max_context_messages (20)
    - Include system prompt for chatbot behavior
    - _Requirements: 5.2_

  - [x] 8.4 Implement _execute_tool_calls helper method
    - Execute each tool call via ToolRegistry
    - Collect tool results
    - Format results for LLM
    - Handle tool execution errors gracefully
    - _Requirements: 6.2, 6.3, 7.4_

  - [ ]* 8.5 Write unit tests for ChatHandler
    - Mock Strands SDK client
    - Test message processing flow
    - Test context building
    - Test tool call execution
    - _Requirements: 2.3, 6.2, 6.3_

  - [ ]* 8.6 Write property tests for tool execution flow
    - **Property 12: Tool calls are executed before final response**
    - **Property 13: Tool results are provided to LLM**
    - **Validates: Requirements 6.2, 6.3**

- [ ] 9. Implement HTTP Server and API endpoints
  - [ ] 9.1 Create FastAPI application with CORS configuration
    - Initialize FastAPI app
    - Configure CORS for frontend origin (http://localhost:3000)
    - Set up request timeout (30 seconds)
    - _Requirements: 2.1_

  - [ ] 9.2 Implement POST /api/chat endpoint
    - Accept ChatRequest body
    - Retrieve or create session
    - Process message via ChatHandler
    - Update session with new messages
    - Return ChatResponse
    - _Requirements: 2.2, 2.3, 2.4_

  - [ ] 9.3 Add error handling middleware
    - Catch all exceptions
    - Log errors with full context
    - Return ErrorResponse with appropriate status codes
    - _Requirements: 7.5_

  - [ ] 9.4 Implement GET /api/health endpoint
    - Check Bedrock connectivity
    - Check backend API connectivity
    - Return HealthResponse with status
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ]* 9.5 Write integration tests for API endpoints
    - Test /api/chat with valid requests
    - Test /api/chat with invalid requests
    - Test /api/health endpoint
    - Test error handling
    - _Requirements: 2.2, 10.1_

  - [ ]* 9.6 Write property tests for API behavior
    - **Property 1: Valid chat requests return success**
    - **Property 20: Health check verifies Bedrock connectivity**
    - **Property 21: Health check verifies backend connectivity**
    - **Property 22: Health status reflects dependency availability**
    - **Validates: Requirements 2.2, 10.2, 10.3, 10.4**

- [ ] 10. Implement logging and error handling
  - [ ] 10.1 Set up structured logging
    - Configure JSON logging format
    - Add request_id to all log entries
    - Set up log levels (ERROR, WARN, INFO, DEBUG)
    - _Requirements: 7.5_

  - [ ] 10.2 Add comprehensive error logging
    - Log all exceptions with stack traces
    - Log failed API calls with details
    - Log retry attempts
    - _Requirements: 7.5_

  - [ ]* 10.3 Write property test for error handling
    - **Property 15: Unexpected errors are logged and handled gracefully**
    - **Validates: Requirements 7.5**

- [ ] 11. Create application entry point
  - [ ] 11.1 Create main.py with FastAPI app initialization
    - Initialize all components (SessionManager, BackendClient, ToolRegistry, ChatHandler)
    - Wire components together
    - Set up background tasks (session cleanup)
    - Configure uvicorn server
    - _Requirements: 1.1, 2.1_

  - [ ] 11.2 Add startup and shutdown event handlers
    - Verify AWS credentials on startup
    - Test backend connectivity on startup
    - Clean up resources on shutdown
    - _Requirements: 1.1, 10.2, 10.3_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 13. Integration and end-to-end testing
  - [ ]* 13.1 Write integration test for complete chat flow
    - Test multi-turn conversation with context
    - Test tool usage (product browsing, cart management)
    - Test session persistence across requests
    - _Requirements: 2.3, 2.4, 5.2, 6.2_

  - [ ]* 13.2 Write integration test for backend communication
    - Test all backend API endpoints through tools
    - Test error handling when backend is unavailable
    - Test retry logic with simulated failures
    - _Requirements: 3.1, 4.1, 7.2, 7.3_

  - [ ]* 13.3 Write integration test for Bedrock integration
    - Test LLM response generation
    - Test tool calling flow
    - Test error handling for Bedrock failures
    - _Requirements: 1.2, 6.1, 6.2, 7.4_

- [ ] 14. Documentation and deployment preparation
  - [ ] 14.1 Create README.md for chatbot service
    - Document setup instructions
    - Document environment variables
    - Document running the service (development and production)
    - Document API endpoints
    - _Requirements: 8.1, 8.2_

  - [ ] 14.2 Create .env.example file
    - Include all required environment variables with descriptions
    - Provide example values (non-sensitive)
    - _Requirements: 8.1_

  - [ ] 14.3 Update root README.md
    - Add chatbot service to project overview
    - Document how to run all three services together
    - Add architecture diagram reference
    - _Requirements: 2.1_

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation uses Python 3.11+ with FastAPI, Strands SDK, and AWS Bedrock Nova Pro
- All components are designed to be testable with clear separation of concerns
- The service runs on port 3002 and integrates with the existing backend on port 3001

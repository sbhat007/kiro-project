"""
Pydantic models for API requests and responses.

This module defines the data models used for HTTP API communication,
including request validation and response serialization.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re


class ChatRequest(BaseModel):
    """Request model for chat endpoint.
    
    Validates user messages and optional session IDs for conversation context.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's chat message"
    )
    session_id: str | None = Field(
        None,
        description="Optional session ID for conversation context (UUID format)"
    )
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str | None) -> str | None:
        """Validate session_id is a valid UUID format if provided."""
        if v is not None:
            # UUID v4 format: 8-4-4-4-12 hex characters
            uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
            if not re.match(uuid_pattern, v.lower()):
                raise ValueError('session_id must be a valid UUID format')
        return v


class ChatResponse(BaseModel):
    """Response model for chat endpoint.
    
    Contains the assistant's response, session ID, and timestamp.
    """
    response: str = Field(..., description="Assistant's response message")
    session_id: str = Field(..., description="Session ID for conversation context")
    timestamp: datetime = Field(..., description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Response model for error cases.
    
    Provides error message and optional additional details.
    """
    error: str = Field(..., description="Error message")
    details: str | None = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Response model for health check endpoint.
    
    Indicates service health status and dependency availability.
    """
    status: str = Field(..., description="Overall health status: 'healthy' or 'unhealthy'")
    bedrock_available: bool = Field(..., description="AWS Bedrock connectivity status")
    backend_available: bool = Field(..., description="Backend API connectivity status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

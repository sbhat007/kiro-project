"""Configuration management for the Shopping Assistant Chatbot.

This module provides configuration loading and validation using Pydantic Settings.
Environment variables are loaded from .env file with validation for required fields.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    All settings can be configured via environment variables or .env file.
    Required fields will raise validation errors if not provided.
    """
    
    # AWS Configuration
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for Bedrock service"
    )
    aws_access_key_id: str = Field(
        ...,
        description="AWS access key ID for authentication"
    )
    aws_secret_access_key: str = Field(
        ...,
        description="AWS secret access key for authentication"
    )
    bedrock_model_id: str = Field(
        default="amazon.nova-pro-v1:0",
        description="Bedrock model identifier"
    )
    
    # Server Configuration
    server_host: str = Field(
        default="0.0.0.0",
        description="Host address for the HTTP server"
    )
    server_port: int = Field(
        default=3002,
        description="Port number for the HTTP server",
        ge=1,
        le=65535
    )
    
    # Backend Configuration
    backend_base_url: str = Field(
        default="http://localhost:3001",
        description="Base URL for the backend API"
    )
    backend_timeout: int = Field(
        default=10,
        description="Timeout in seconds for backend API requests",
        ge=1
    )
    
    # Session Configuration
    session_ttl_minutes: int = Field(
        default=30,
        description="Session time-to-live in minutes",
        ge=1
    )
    max_context_messages: int = Field(
        default=20,
        description="Maximum number of messages to include in context window",
        ge=1
    )
    
    # LLM Configuration
    llm_temperature: float = Field(
        default=0.7,
        description="Temperature for LLM generation (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    llm_max_tokens: int = Field(
        default=2048,
        description="Maximum tokens for LLM response",
        ge=1
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("backend_base_url")
    @classmethod
    def validate_backend_url(cls, v: str) -> str:
        """Ensure backend URL doesn't end with trailing slash."""
        return v.rstrip("/")
    
    @field_validator("bedrock_model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        """Ensure model ID is not empty."""
        if not v or not v.strip():
            raise ValueError("bedrock_model_id cannot be empty")
        return v.strip()


# Global settings instance
settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance.
    
    Returns:
        Settings: The application settings instance
        
    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    global settings
    if settings is None:
        settings = Settings()
    return settings

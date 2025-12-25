"""Pydantic schemas for chat session and message API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatSessionCreateRequest(BaseModel):
    """Request schema for creating a new chat session."""

    flow_id: UUID = Field(..., description="Flow ID for this chat session")
    session_name: str = Field(..., description="Name for the chat session/tab")
    user_id: UUID | None = Field(None, description="User ID (optional for anonymous sessions)")


class ChatSessionResponse(BaseModel):
    """Response schema for chat session."""

    session_id: UUID = Field(..., description="Unique session ID")
    session_name: str = Field(..., description="Name of the chat session")
    flow_id: UUID = Field(..., description="Associated flow ID")
    user_id: UUID | None = Field(None, description="User ID if authenticated")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Whether session is active")


class ChatWidgetRequest(BaseModel):
    """Request schema for chat widget endpoint."""

    session_id: UUID = Field(..., description="Chat session ID")
    message: str = Field(..., description="User's message")
    flow_id: UUID = Field(..., description="Flow ID to use for processing")


class ChatMessageResponse(BaseModel):
    """Response schema for a single chat message."""

    id: UUID = Field(..., description="Message ID")
    session_id: UUID = Field(..., description="Session ID")
    user_message: str = Field(..., description="User's message")
    assistant_message: str = Field(..., description="Assistant's response")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class ChatHistoryResponse(BaseModel):
    """Response schema for chat history."""

    session_id: UUID = Field(..., description="Session ID")
    session_name: str = Field(..., description="Session name")
    messages: list[ChatMessageResponse] = Field(default_factory=list, description="List of messages")
    total_messages: int = Field(..., description="Total number of messages")

"""Chat Session database model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Text
from sqlmodel import Column, Field, SQLModel


class ChatSessionBase(SQLModel):
    """Base model for chat sessions."""

    session_name: str = Field(sa_column=Column(Text), description="Name of the chat session/tab")
    flow_id: UUID = Field(foreign_key="flow.id", description="Flow associated with this chat session")
    user_id: UUID | None = Field(default=None, foreign_key="user.id", nullable=True, description="User who owns this session")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether the session is active")


class ChatSession(ChatSessionBase, table=True):  # type: ignore[call-arg]
    """Chat session table for managing chat tabs."""

    __tablename__ = "chat_session"

    id: UUID = Field(default_factory=uuid4, primary_key=True)


class ChatSessionCreate(ChatSessionBase):
    """Schema for creating a new chat session."""

    pass


class ChatSessionRead(ChatSessionBase):
    """Schema for reading a chat session."""

    id: UUID


class ChatSessionUpdate(SQLModel):
    """Schema for updating a chat session."""

    session_name: str | None = None
    is_active: bool | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

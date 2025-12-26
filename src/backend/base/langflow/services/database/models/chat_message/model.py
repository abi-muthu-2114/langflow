"""Chat Message database model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Text
from sqlmodel import JSON, Column, Field, SQLModel


class ChatMessageBase(SQLModel):
    """Base model for chat messages."""

    session_id: UUID = Field(foreign_key="chat_session.id", description="Chat session this message belongs to")
    flow_id: UUID = Field(foreign_key="flow.id", description="Flow used for this message")
    user_message: str = Field(sa_column=Column(Text), description="User's message")
    assistant_message: str = Field(sa_column=Column(Text), description="Assistant's response")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Message timestamp")
    extra_metadata: dict | None = Field(default_factory=dict, sa_column=Column("metadata", JSON), description="Additional metadata (tokens, model, etc.)")


class ChatMessage(ChatMessageBase, table=True):  # type: ignore[call-arg]
    """Chat message table for storing conversation history."""

    __tablename__ = "chat_message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)


class ChatMessageCreate(ChatMessageBase):
    """Schema for creating a new chat message."""

    pass


class ChatMessageRead(ChatMessageBase):
    """Schema for reading a chat message."""

    id: UUID

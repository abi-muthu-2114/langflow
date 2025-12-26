"""Widget Session database model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Text
from sqlmodel import Column, Field, SQLModel


class WidgetSessionBase(SQLModel):
    """Base model for widget sessions."""

    session_name: str = Field(sa_column=Column(Text), description="Name of the chat session/tab")
    flow_id: UUID | None = Field(default=None, foreign_key="flow.id", description="Flow associated with this chat session")
    user_id: UUID | None = Field(default=None, foreign_key="user.id", nullable=True, description="User who owns this session")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether the session is active")


class WidgetSession(WidgetSessionBase, table=True):  # type: ignore[call-arg]
    """Widget session table for managing chat tabs."""

    __tablename__ = "widget_session"

    id: UUID = Field(default_factory=uuid4, primary_key=True)


class WidgetSessionCreate(WidgetSessionBase):
    """Schema for creating a new widget session."""

    pass


class WidgetSessionRead(WidgetSessionBase):
    """Schema for reading a widget session."""

    id: UUID

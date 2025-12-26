"""Widget Message database model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Text
from sqlmodel import JSON, Column, Field, SQLModel


class WidgetMessageBase(SQLModel):
    """Base model for widget messages."""

    session_id: UUID = Field(foreign_key="widget_session.id", description="Widget session this message belongs to")
    flow_id: UUID = Field(foreign_key="flow.id", description="Flow used for this message")
    user_message: str = Field(sa_column=Column(Text), description="User's message")
    assistant_message: str = Field(sa_column=Column(Text), description="Assistant's response")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Message timestamp")
    extra_metadata: dict | None = Field(default_factory=dict, sa_column=Column("metadata", JSON), description="Additional metadata")


class WidgetMessage(WidgetMessageBase, table=True):  # type: ignore[call-arg]
    """Widget message table for storing conversation history."""

    __tablename__ = "widget_message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)


class WidgetMessageCreate(WidgetMessageBase):
    """Schema for creating a new widget message."""

    pass


class WidgetMessageRead(WidgetMessageBase):
    """Schema for reading a widget message."""

    id: UUID

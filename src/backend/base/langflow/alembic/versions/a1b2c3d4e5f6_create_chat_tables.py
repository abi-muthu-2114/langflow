"""Create chat session and chat message tables

Revision ID: a1b2c3d4e5f6
Revises: fd531f8868b1
Create Date: 2025-12-26 03:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

from langflow.utils import migration

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "fd531f8868b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create chat_session and chat_message tables."""
    conn = op.get_bind()
    
    # Create chat_session table
    if not migration.table_exists("chat_session", conn):
        op.create_table(
            "chat_session",
            sa.Column("session_name", sa.Text(), nullable=False),
            sa.Column("flow_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
            sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
            sa.ForeignKeyConstraint(
                ["flow_id"],
                ["flow.id"],
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["user.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        # Create indexes for better query performance
        op.create_index(op.f("ix_chat_session_flow_id"), "chat_session", ["flow_id"], unique=False)
        op.create_index(op.f("ix_chat_session_user_id"), "chat_session", ["user_id"], unique=False)
        op.create_index(op.f("ix_chat_session_created_at"), "chat_session", ["created_at"], unique=False)
    
    # Create chat_message table
    if not migration.table_exists("chat_message", conn):
        op.create_table(
            "chat_message",
            sa.Column("session_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
            sa.Column("flow_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
            sa.Column("user_message", sa.Text(), nullable=False),
            sa.Column("assistant_message", sa.Text(), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=False),
            sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
            sa.ForeignKeyConstraint(
                ["session_id"],
                ["chat_session.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["flow_id"],
                ["flow.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        # Create indexes for better query performance
        op.create_index(op.f("ix_chat_message_session_id"), "chat_message", ["session_id"], unique=False)
        op.create_index(op.f("ix_chat_message_flow_id"), "chat_message", ["flow_id"], unique=False)
        op.create_index(op.f("ix_chat_message_timestamp"), "chat_message", ["timestamp"], unique=False)


def downgrade() -> None:
    """Drop chat_session and chat_message tables."""
    conn = op.get_bind()
    
    # Drop chat_message table first (due to foreign key constraint)
    if migration.table_exists("chat_message", conn):
        op.drop_index(op.f("ix_chat_message_timestamp"), table_name="chat_message")
        op.drop_index(op.f("ix_chat_message_flow_id"), table_name="chat_message")
        op.drop_index(op.f("ix_chat_message_session_id"), table_name="chat_message")
        op.drop_table("chat_message")
    
    # Drop chat_session table
    if migration.table_exists("chat_session", conn):
        op.drop_index(op.f("ix_chat_session_created_at"), table_name="chat_session")
        op.drop_index(op.f("ix_chat_session_user_id"), table_name="chat_session")
        op.drop_index(op.f("ix_chat_session_flow_id"), table_name="chat_session")
        op.drop_table("chat_session")

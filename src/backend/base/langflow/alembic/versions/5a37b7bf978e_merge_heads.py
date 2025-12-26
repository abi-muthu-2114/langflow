"""'merge_heads'

Revision ID: 5a37b7bf978e
Revises: 182e5471b900, a1b2c3d4e5f6
Create Date: 2025-12-26 09:43:06.187937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.engine.reflection import Inspector
from langflow.utils import migration


# revision identifiers, used by Alembic.
revision: str = '5a37b7bf978e'
down_revision: Union[str, None] = ('182e5471b900', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    pass


def downgrade() -> None:
    conn = op.get_bind()
    pass

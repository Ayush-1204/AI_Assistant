"""Add is_pinned to conversations

Revision ID: 8bafe7270f9e
Revises: 9998a62ae490
Create Date: 2026-07-15 18:21:43.504509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8bafe7270f9e'
down_revision: Union[str, Sequence[str], None] = '9998a62ae490'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('conversations', sa.Column('is_pinned', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('conversations', 'is_pinned')

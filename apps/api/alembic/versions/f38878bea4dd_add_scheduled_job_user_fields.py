"""add_scheduled_job_user_fields

Revision ID: f38878bea4dd
Revises: 8bafe7270f9e
Create Date: 2026-07-23 20:46:24.432078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f38878bea4dd'
down_revision: Union[str, Sequence[str], None] = '8bafe7270f9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('scheduled_jobs', sa.Column('label', sa.String(length=255), nullable=True))
    op.add_column('scheduled_jobs', sa.Column('is_user_defined', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('scheduled_jobs', sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('scheduled_jobs', sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('scheduled_jobs', 'next_run_at')
    op.drop_column('scheduled_jobs', 'is_enabled')
    op.drop_column('scheduled_jobs', 'is_user_defined')
    op.drop_column('scheduled_jobs', 'label')

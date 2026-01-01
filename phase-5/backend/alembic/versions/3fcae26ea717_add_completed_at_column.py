"""add_completed_at_column

Revision ID: 3fcae26ea717
Revises: 0eeaf6a35d2a
Create Date: 2026-01-01 18:10:12.997000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fcae26ea717'
down_revision: Union[str, Sequence[str], None] = '0eeaf6a35d2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add completed_at column to tasks table (nullable, backward compatible)
    op.add_column('tasks', sa.Column('completed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove completed_at column
    op.drop_column('tasks', 'completed_at')

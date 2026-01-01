"""add_phase5_fields_recurring_reminders

Revision ID: f39859e829dd
Revises: 3fcae26ea717
Create Date: 2026-01-01 18:12:00.943149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f39859e829dd'
down_revision: Union[str, Sequence[str], None] = '3fcae26ea717'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

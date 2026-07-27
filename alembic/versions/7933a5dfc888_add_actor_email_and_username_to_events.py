"""add actor email and username to events

Revision ID: 7933a5dfc888
Revises: 13ec84a90633
Create Date: 2026-07-26 04:09:51.708527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7933a5dfc888'
down_revision: Union[str, Sequence[str], None] = '13ec84a90633'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('events', sa.Column('actor_email', sa.String(), nullable=True))
    op.add_column('events', sa.Column('actor_username', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('events', 'actor_username')
    op.drop_column('events', 'actor_email')
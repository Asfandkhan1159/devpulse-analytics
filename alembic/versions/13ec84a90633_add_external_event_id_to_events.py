"""add external_event_id to events for idempotency

Revision ID: 13ec84a90633
Revises: d99efb8e9cd3
Create Date: 2026-06-18 00:28:23.606653
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13ec84a90633'
down_revision: str | None = 'd99efb8e9cd3'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Add the column
    op.add_column('events', sa.Column('external_event_id', sa.String(), nullable=True))
    
    # Index for performance
    op.create_index(op.f('ix_events_external_event_id'), 'events', ['external_event_id'], unique=False)
    
    # CRITICAL: Unique constraint to prevent duplicate events
    op.create_unique_constraint(
        'uq_events_external', 
        'events', 
        ['project_id', 'provider', 'external_event_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_events_external', 'events', type_='unique')
    op.drop_index(op.f('ix_events_external_event_id'), table_name='events')
    op.drop_column('events', 'external_event_id')
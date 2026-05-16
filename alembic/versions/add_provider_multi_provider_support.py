"""add provider and external_id for multi-provider support

Revision ID: a1b2c3d4e5f6
Revises: 3230c36df9d5
Create Date: 2026-05-16 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3230c36df9d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. add external_id to project_table
    op.add_column('project_table', sa.Column('external_id', sa.String(), nullable=True))
    op.create_index('ix_project_table_external_id', 'project_table', ['external_id'])

    # 2. add provider to project_table
    op.add_column('project_table', sa.Column('provider', sa.String(), nullable=True))
    op.create_index('ix_project_table_provider', 'project_table', ['provider'])

    # 3. copy gitlab_project_id into external_id
    op.execute("UPDATE project_table SET external_id = CAST(gitlab_project_id AS VARCHAR)")

    # 4. set provider = 'gitlab' on all existing projects
    op.execute("UPDATE project_table SET provider = 'gitlab'")

    # 5. drop old gitlab_project_id index and column
    op.drop_index('ix_project_table_gitlab_project_id', table_name='project_table')
    op.drop_column('project_table', 'gitlab_project_id')

    # 6. add provider to events
    op.add_column('events', sa.Column('provider', sa.String(), nullable=True))
    op.create_index('ix_events_provider', 'events', ['provider'])

    # 7. set provider = 'gitlab' on all existing events
    op.execute("UPDATE events SET provider = 'gitlab'")


def downgrade() -> None:
    # reverse everything in opposite order

    # 1. remove provider from events
    op.drop_index('ix_events_provider', table_name='events')
    op.drop_column('events', 'provider')

    # 2. re-add gitlab_project_id to project_table
    op.add_column('project_table', sa.Column('gitlab_project_id', sa.Integer(), nullable=True))
    op.create_index('ix_project_table_gitlab_project_id', 'project_table', ['gitlab_project_id'])

    # 3. copy external_id back into gitlab_project_id
    op.execute("UPDATE project_table SET gitlab_project_id = CAST(external_id AS INTEGER)")

    # 4. drop provider and external_id from project_table
    op.drop_index('ix_project_table_provider', table_name='project_table')
    op.drop_column('project_table', 'provider')
    op.drop_index('ix_project_table_external_id', table_name='project_table')
    op.drop_column('project_table', 'external_id')
"""add resources to lessons, remove video_url and resources from courses

Revision ID: c2a7e9f81234
Revises: b156f788f423
Create Date: 2026-04-11 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c2a7e9f81234'
down_revision: Union[str, Sequence[str]] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add resources JSONB to lessons, drop video_url and resources from courses."""
    # Add resources column to lessons
    op.add_column('lessons', sa.Column('resources', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Drop video_url and resources from courses
    op.drop_column('courses', 'video_url')
    op.drop_column('courses', 'resources')


def downgrade() -> None:
    """Reverse: re-add video_url and resources to courses, drop resources from lessons."""
    op.add_column('courses', sa.Column('resources', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('courses', sa.Column('video_url', sa.Text(), nullable=True))

    op.drop_column('lessons', 'resources')

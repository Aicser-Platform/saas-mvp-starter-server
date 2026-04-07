"""add subscription and stripe fields to users

Revision ID: c2d3e4f5a6b7
Revises: b156f788f423
Create Date: 2026-03-30 08:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = 'b156f788f423'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Stripe and subscription fields to users table."""
    op.add_column('users', sa.Column('stripe_customer_id', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('subscription_tier', sa.Text(), server_default='free', nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.Text(), server_default='inactive', nullable=True))
    op.add_column('users', sa.Column('subscription_start_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('subscription_end_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove Stripe and subscription fields from users table."""
    op.drop_column('users', 'subscription_end_date')
    op.drop_column('users', 'subscription_start_date')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'subscription_tier')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')

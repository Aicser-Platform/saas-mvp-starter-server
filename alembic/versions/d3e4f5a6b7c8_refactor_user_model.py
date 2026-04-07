"""refactor user model - move subscription and stripe fields to proper tables

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-03-30 09:48:00.000000

Migration summary:
  1. Migrate stripe_customer_id → billing_accounts (provider='stripe')
  2. Migrate stripe_subscription_id, subscription_tier/status/dates → subscriptions
  3. Drop the 6 columns from users
  4. Add provider_subscription_id to subscriptions
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, Sequence[str], None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── Step 1: Add provider_subscription_id to subscriptions ───────────────
    op.add_column('subscriptions', sa.Column('provider_subscription_id', sa.Text(), nullable=True))

    # ── Step 2: Migrate stripe_customer_id → billing_accounts ───────────────
    # For each user with a stripe_customer_id, create a billing_account record
    # (only if one doesn't already exist for stripe provider)
    conn.execute(text("""
        INSERT INTO billing_accounts (id, user_id, provider, customer_id, created_at)
        SELECT
            uuid_generate_v4(),
            u.id,
            'stripe',
            u.stripe_customer_id,
            NOW()
        FROM users u
        WHERE u.stripe_customer_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM billing_accounts ba
              WHERE ba.user_id = u.id AND ba.provider = 'stripe'
          )
    """))

    # ── Step 3: Migrate subscription fields → subscriptions ─────────────────
    # Check if plans table has entries; if so, try to match by subscription_tier
    # We only create subscription records for users with an active/non-inactive status
    conn.execute(text("""
        INSERT INTO subscriptions (
            id, user_id, plan_id,
            status, provider_subscription_id,
            current_period_start, current_period_end,
            created_at, updated_at
        )
        SELECT
            uuid_generate_v4(),
            u.id,
            p.id,
            COALESCE(u.subscription_status, 'inactive'),
            u.stripe_subscription_id,
            u.subscription_start_date,
            u.subscription_end_date,
            NOW(),
            NOW()
        FROM users u
        JOIN plans p ON LOWER(p.name) = LOWER(u.subscription_tier)
        WHERE u.subscription_tier IS NOT NULL
          AND u.subscription_tier != 'free'
          AND u.subscription_status IN ('active', 'past_due', 'trialing')
          AND NOT EXISTS (
              SELECT 1 FROM subscriptions s
              WHERE s.user_id = u.id AND s.status IN ('active', 'trialing', 'past_due')
          )
    """))

    # ── Step 4: Drop the 6 columns from users ───────────────────────────────
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'subscription_tier')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'subscription_start_date')
    op.drop_column('users', 'subscription_end_date')


def downgrade() -> None:
    # Re-add the 6 columns to users
    op.add_column('users', sa.Column('stripe_customer_id', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('subscription_tier', sa.Text(), server_default='free', nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.Text(), server_default='inactive', nullable=True))
    op.add_column('users', sa.Column('subscription_start_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('subscription_end_date', sa.DateTime(timezone=True), nullable=True))

    # Remove provider_subscription_id from subscriptions
    op.drop_column('subscriptions', 'provider_subscription_id')

"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('subscription_tier', sa.Enum('free', 'pro', 'elite', name='subscriptiontier'), nullable=True, default='free'),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('subscription_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_alerts', sa.Boolean(), default=True),
        sa.Column('push_alerts', sa.Boolean(), default=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=True)

    # Signals table
    op.create_table(
        'signals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_type', sa.Enum('crypto', 'stock', 'forex', 'commodity', name='assettype'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('pair', sa.String(20), nullable=False),
        sa.Column('signal_type', sa.Enum('buy', 'sell', 'hold', name='signaltype'), nullable=False),
        sa.Column('oracle_score', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('target_price', sa.Float(), nullable=False),
        sa.Column('stop_loss', sa.Float(), nullable=False),
        sa.Column('risk_reward_ratio', sa.Float(), nullable=False),
        sa.Column('position_size_suggestion', sa.Float(), nullable=True),
        sa.Column('reasoning_summary', sa.Text(), nullable=False),
        sa.Column('reasoning_factors', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('input_snapshot', sa.JSON(), nullable=False),
        sa.Column('data_sources', sa.JSON(), nullable=False),
        sa.Column('timeframe', sa.String(20), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('active', 'hit_target', 'hit_stop', 'expired', 'cancelled', name='signalstatus'), default='active'),
        sa.Column('outcome_price', sa.Float(), nullable=True),
        sa.Column('outcome_pnl_percent', sa.Float(), nullable=True),
        sa.Column('outcome_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_delivered', sa.Boolean(), default=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_signals_id', 'signals', ['id'])
    op.create_index('ix_signals_symbol', 'signals', ['symbol'])
    op.create_index('ix_signals_created_at', 'signals', ['created_at'])
    op.create_index('ix_signals_status', 'signals', ['status'])

    # Signal deliveries table
    op.create_table(
        'signal_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('signal_id', sa.Integer(), sa.ForeignKey('signals.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('delivery_method', sa.String(20), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_signal_deliveries_id', 'signal_deliveries', ['id'])

def downgrade() -> None:
    op.drop_table('signal_deliveries')
    op.drop_table('signals')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
    op.execute('DROP TYPE IF EXISTS assettype')
    op.execute('DROP TYPE IF EXISTS signaltype')
    op.execute('DROP TYPE IF EXISTS signalstatus')

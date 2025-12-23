"""Add phone column to users

Revision ID: add_phone_001
Revises: 
Create Date: 2024-12-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_phone_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone')

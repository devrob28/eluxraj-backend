"""merge heads

Revision ID: 44fb429d2bdc
Revises: 001, add_phone_001
Create Date: 2026-03-06 19:10:45.903437
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '44fb429d2bdc'
down_revision: Union[str, None] = ('001', 'add_phone_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

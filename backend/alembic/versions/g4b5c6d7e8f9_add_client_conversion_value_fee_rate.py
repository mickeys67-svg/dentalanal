"""Add conversion_value and fee_rate to clients table

Revision ID: g4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-02-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g4b5c6d7e8f9'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('conversion_value', sa.Float(), nullable=True))
    op.add_column('clients', sa.Column('fee_rate', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('clients', 'fee_rate')
    op.drop_column('clients', 'conversion_value')

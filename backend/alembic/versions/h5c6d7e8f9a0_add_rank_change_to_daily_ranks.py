"""Add rank_change column to daily_ranks table

Revision ID: h5c6d7e8f9a0
Revises: g4b5c6d7e8f9
Create Date: 2026-02-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h5c6d7e8f9a0'
down_revision: Union[str, None] = 'g4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('daily_ranks', sa.Column('rank_change', sa.Integer(), server_default='0', nullable=True))


def downgrade() -> None:
    op.drop_column('daily_ranks', 'rank_change')

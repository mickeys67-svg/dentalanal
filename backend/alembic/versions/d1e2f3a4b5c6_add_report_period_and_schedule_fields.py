"""Add period_start, period_end, generated_at, schedule to reports table

Revision ID: d1e2f3a4b5c6
Revises: c3f8a912b045
Create Date: 2026-02-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c3f8a912b045'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('period_start', sa.Date(), nullable=True))
    op.add_column('reports', sa.Column('period_end', sa.Date(), nullable=True))
    op.add_column('reports', sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('reports', sa.Column('schedule', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'schedule')
    op.drop_column('reports', 'generated_at')
    op.drop_column('reports', 'period_end')
    op.drop_column('reports', 'period_start')

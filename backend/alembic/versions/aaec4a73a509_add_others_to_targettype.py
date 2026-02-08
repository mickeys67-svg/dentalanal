"""Add OTHERS to TargetType

Revision ID: aaec4a73a509
Revises: 592a283fdda1
Create Date: 2026-02-08 12:30:50.782211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aaec4a73a509'
down_revision: Union[str, None] = '592a283fdda1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Manual ENUM update for PostgreSQL
    op.execute("ALTER TYPE targettype ADD VALUE 'OTHERS'")


def downgrade() -> None:
    # Downgrade not easily supported for ENUM, skipping
    pass

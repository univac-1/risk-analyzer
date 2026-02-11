"""add public_nuisance to riskcategory enum

Revision ID: 002
Revises: 001
Create Date: 2026-02-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE riskcategory ADD VALUE IF NOT EXISTS 'public_nuisance'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # A full type recreation would be required; skipping for now.
    pass

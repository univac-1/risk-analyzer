"""add public_nuisance to riskcategory enum

Revision ID: 002
Revises: 001
Create Date: 2026-02-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE は PostgreSQL のトランザクション内では実行できないため、
    # 明示的に COMMIT してトランザクション外で実行する
    conn = op.get_bind()
    conn.execute(sa.text("COMMIT"))
    conn.execute(sa.text("ALTER TYPE riskcategory ADD VALUE IF NOT EXISTS 'public_nuisance'"))


def downgrade() -> None:
    # PostgreSQL は enum 値の削除を直接サポートしないため省略
    pass

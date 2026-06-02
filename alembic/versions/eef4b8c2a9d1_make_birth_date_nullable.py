"""make birth_date nullable

Revision ID: eef4b8c2a9d1
Revises: 48d5f3a4582f
Create Date: 2026-05-12

Google 로그인 시 생년월일 미수집 → Users.birth_date NULL 허용 (온보딩에서 수집).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "eef4b8c2a9d1"
down_revision: Union[str, None] = "48d5f3a4582f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "Users",
        "birth_date",
        existing_type=sa.Date(),
        nullable=True,
        existing_nullable=False,
    )


def downgrade() -> None:
    # birth_date 가 NULL 인 행이 있으면 downgrade 실패할 수 있음
    op.alter_column(
        "Users",
        "birth_date",
        existing_type=sa.Date(),
        nullable=False,
        existing_nullable=True,
    )

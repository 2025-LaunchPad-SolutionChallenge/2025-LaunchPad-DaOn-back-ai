"""add avg_7d_need_score and recent_3d_zero_task_count to recovery_features

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recovery_features",
        sa.Column("avg_7d_need_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "recovery_features",
        sa.Column("recent_3d_zero_task_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("recovery_features", "recent_3d_zero_task_count")
    op.drop_column("recovery_features", "avg_7d_need_score")

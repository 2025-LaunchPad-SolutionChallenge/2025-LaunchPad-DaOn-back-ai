"""add avg_7d_available_time, recent_3d_counts to recovery_features; add raw_stage to recovery_outputs

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recovery_features",
        sa.Column("avg_7d_available_time", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "recovery_features",
        sa.Column("recent_3d_need_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "recovery_features",
        sa.Column("recent_3d_no_outing_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "recovery_outputs",
        sa.Column("raw_stage", sa.String(20), nullable=False, server_default="CHAOS"),
    )


def downgrade() -> None:
    op.drop_column("recovery_outputs", "raw_stage")
    op.drop_column("recovery_features", "recent_3d_no_outing_count")
    op.drop_column("recovery_features", "recent_3d_need_count")
    op.drop_column("recovery_features", "avg_7d_available_time")

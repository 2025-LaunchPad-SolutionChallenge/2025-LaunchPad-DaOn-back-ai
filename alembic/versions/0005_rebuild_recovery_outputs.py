"""rebuild recovery_outputs: replace recovery_stage_id FK with predicted_stage + tasks

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 기존 FK 컬럼 제거
    op.drop_constraint(
        "recovery_outputs_ibfk_2",   # MySQL 기본 FK 이름, 환경에 따라 다를 수 있음
        "recovery_outputs",
        type_="foreignkey",
    )
    op.drop_column("recovery_outputs", "recovery_stage_id")

    # 신규 컬럼 추가
    op.add_column(
        "recovery_outputs",
        sa.Column("predicted_stage", sa.String(20), nullable=False),
    )
    op.add_column(
        "recovery_outputs",
        sa.Column("task_1", sa.String(255), nullable=False, server_default=""),
    )
    op.add_column(
        "recovery_outputs",
        sa.Column("task_2", sa.String(255), nullable=False, server_default=""),
    )
    op.add_column(
        "recovery_outputs",
        sa.Column("task_3", sa.String(255), nullable=False, server_default=""),
    )

    # UNIQUE 제약 추가
    op.create_unique_constraint(
        "uq_recovery_output_user_date",
        "recovery_outputs",
        ["user__disaster_id", "state_date"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_recovery_output_user_date", "recovery_outputs", type_="unique"
    )
    op.drop_column("recovery_outputs", "task_3")
    op.drop_column("recovery_outputs", "task_2")
    op.drop_column("recovery_outputs", "task_1")
    op.drop_column("recovery_outputs", "predicted_stage")

    op.add_column(
        "recovery_outputs",
        sa.Column("recovery_stage_id", sa.Integer(), nullable=False),
    )
    op.create_foreign_key(
        "recovery_outputs_ibfk_2",
        "recovery_outputs",
        "recovery_stage_masters",
        ["recovery_stage_id"],
        ["recovery_stage_id"],
    )

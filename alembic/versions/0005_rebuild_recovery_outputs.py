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
    # recovery_stage_id를 참조하는 FK 이름을 동적으로 찾아 삭제
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fks = inspector.get_foreign_keys("recovery_outputs")
    fk_name = next(
        (fk["name"] for fk in fks if "recovery_stage_id" in fk["constrained_columns"]),
        None,
    )
    if fk_name:
        op.drop_constraint(fk_name, "recovery_outputs", type_="foreignkey")
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

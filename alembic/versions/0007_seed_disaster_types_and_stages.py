"""seed disaster_types and recovery_stage_masters

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_disaster_types = sa.table(
    "disaster_types",
    sa.column("disaster_code", sa.String),
    sa.column("disaster_name", sa.String),
)

_stages = sa.table(
    "recovery_stage_masters",
    sa.column("stage_code", sa.String),
    sa.column("stage_name", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(
        _disaster_types,
        [
            {"disaster_code": "FLOOD", "disaster_name": "홍수"},
            {"disaster_code": "TYPHOON", "disaster_name": "태풍"},
            {"disaster_code": "EARTHQUAKE", "disaster_name": "지진"},
            {"disaster_code": "FIRE", "disaster_name": "화재"},
        ],
    )
    op.bulk_insert(
        _stages,
        [
            {"stage_code": "CHAOS", "stage_name": "혼란"},
            {"stage_code": "STAGNANT", "stage_name": "침체"},
            {"stage_code": "ATTEMPTING", "stage_name": "시도"},
            {"stage_code": "STABLE", "stage_name": "안정"},
            {"stage_code": "RECOVERY_MAINTAINED", "stage_name": "회복 유지"},
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM recovery_stage_masters WHERE stage_code IN "
        "('CHAOS','STAGNANT','ATTEMPTING','STABLE','RECOVERY_MAINTAINED')"
    )
    op.execute(
        "DELETE FROM disaster_types WHERE disaster_code IN "
        "('FLOOD','TYPHOON','EARTHQUAKE','FIRE')"
    )

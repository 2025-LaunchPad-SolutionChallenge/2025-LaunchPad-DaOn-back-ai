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
    op.execute(
        """
        INSERT INTO disaster_types (disaster_code, disaster_name)
        VALUES
            ('FLOOD', '홍수'),
            ('TYPHOON', '태풍'),
            ('EARTHQUAKE', '지진'),
            ('FIRE', '화재')
        ON DUPLICATE KEY UPDATE disaster_name = VALUES(disaster_name)
        """
    )
    op.execute(
        """
        INSERT INTO recovery_stage_masters (stage_code, stage_name)
        VALUES
            ('CHAOS', '혼란'),
            ('STAGNANT', '침체'),
            ('ATTEMPTING', '시도'),
            ('STABLE', '안정'),
            ('RECOVERY_MAINTAINED', '회복 유지')
        ON DUPLICATE KEY UPDATE stage_name = VALUES(stage_name)
        """
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

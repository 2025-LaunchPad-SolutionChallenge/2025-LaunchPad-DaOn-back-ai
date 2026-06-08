"""add psychological_anxiety and onboarding_risk_level to disaster_impacts

Revision ID: 0004
Revises: eef4b8c2a9d1
Create Date: 2026-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "eef4b8c2a9d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "disaster_impacts",
        sa.Column("psychological_anxiety", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "disaster_impacts",
        sa.Column("onboarding_risk_level", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("disaster_impacts", "onboarding_risk_level")
    op.drop_column("disaster_impacts", "psychological_anxiety")

"""add residence verification status and logs

Revision ID: 0010
Revises: 9c2d4ab7e1f0
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "9c2d4ab7e1f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "residence_verification",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("disaster_latitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("disaster_longitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("last_current_lat", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("last_current_lng", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("last_address", sa.String(length=255), nullable=True),
        sa.Column("last_distance_km", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("threshold_km", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("verification_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["Users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_residence_verification_user_id",
        "residence_verification",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "residence_verification_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_latitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("current_longitude", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("distance_km", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("is_success", sa.Boolean(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["Users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_residence_verification_log_user_id",
        "residence_verification_log",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_residence_verification_log_user_id", table_name="residence_verification_log")
    op.drop_table("residence_verification_log")
    op.drop_index("ix_residence_verification_user_id", table_name="residence_verification")
    op.drop_table("residence_verification")

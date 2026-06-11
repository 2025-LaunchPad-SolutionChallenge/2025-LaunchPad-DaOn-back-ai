"""add location columns to user_disasters

Revision ID: 0013
Revises: 0012
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: Union[str, Sequence[str], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("user_disasters")}

    if "latitude" not in existing:
        op.add_column("user_disasters", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    if "longitude" not in existing:
        op.add_column("user_disasters", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))
    if "address" not in existing:
        op.add_column("user_disasters", sa.Column("address", sa.String(255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("user_disasters")}

    if "address" in existing:
        op.drop_column("user_disasters", "address")
    if "longitude" in existing:
        op.drop_column("user_disasters", "longitude")
    if "latitude" in existing:
        op.drop_column("user_disasters", "latitude")

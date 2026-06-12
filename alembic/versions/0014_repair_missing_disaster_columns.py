"""repair missing disaster columns after duplicate revision conflict

Revision ID: 0014
Revises: 0013
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014"
down_revision: Union[str, Sequence[str], None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    impact_columns = {col["name"] for col in inspector.get_columns("disaster_impacts")}
    if "special_notes" not in impact_columns:
        op.add_column("disaster_impacts", sa.Column("special_notes", sa.Text(), nullable=True))

    disaster_columns = {col["name"] for col in inspector.get_columns("user_disasters")}
    if "latitude" not in disaster_columns:
        op.add_column("user_disasters", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    if "longitude" not in disaster_columns:
        op.add_column("user_disasters", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))
    if "address" not in disaster_columns:
        op.add_column("user_disasters", sa.Column("address", sa.String(255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    impact_columns = {col["name"] for col in inspector.get_columns("disaster_impacts")}
    if "special_notes" in impact_columns:
        op.drop_column("disaster_impacts", "special_notes")

    disaster_columns = {col["name"] for col in inspector.get_columns("user_disasters")}
    if "address" in disaster_columns:
        op.drop_column("user_disasters", "address")
    if "longitude" in disaster_columns:
        op.drop_column("user_disasters", "longitude")
    if "latitude" in disaster_columns:
        op.drop_column("user_disasters", "latitude")

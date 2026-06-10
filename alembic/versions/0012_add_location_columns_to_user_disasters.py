"""add location columns to user_disasters

Revision ID: 0012
Revises: 0011
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012"
down_revision: Union[str, Sequence[str], None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_disasters", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("user_disasters", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("user_disasters", sa.Column("address", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("user_disasters", "address")
    op.drop_column("user_disasters", "longitude")
    op.drop_column("user_disasters", "latitude")

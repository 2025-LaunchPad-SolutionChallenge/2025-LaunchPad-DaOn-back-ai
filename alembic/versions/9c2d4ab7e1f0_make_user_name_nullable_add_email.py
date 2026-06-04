"""make user name nullable and add email

Revision ID: 9c2d4ab7e1f0
Revises: f7a8b9c0d1e2
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9c2d4ab7e1f0"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("Users", "name", existing_type=sa.String(length=255), nullable=True)
    op.add_column("Users", sa.Column("email", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("Users", "email")
    op.alter_column("Users", "name", existing_type=sa.String(length=255), nullable=False)

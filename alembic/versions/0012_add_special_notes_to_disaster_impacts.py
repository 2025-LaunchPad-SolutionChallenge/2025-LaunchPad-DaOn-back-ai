"""add special_notes to disaster_impacts

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "disaster_impacts",
        sa.Column("special_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("disaster_impacts", "special_notes")

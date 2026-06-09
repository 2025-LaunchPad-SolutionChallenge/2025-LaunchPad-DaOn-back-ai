"""merge heads 0008 and 0010

Revision ID: 0011
Revises: 0008, 0010
"""

from typing import Sequence, Union

revision: str = "0011"
down_revision: Union[str, Sequence[str], None] = ("0008", "0010")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

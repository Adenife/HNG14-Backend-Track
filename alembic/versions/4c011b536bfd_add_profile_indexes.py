"""add_profile_indexes

Revision ID: 4c011b536bfd
Revises: 58abf52992b5
Create Date: 2026-05-05 12:30:48.121699

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '4c011b536bfd'
down_revision: Union[str, Sequence[str], None] = '58abf52992b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

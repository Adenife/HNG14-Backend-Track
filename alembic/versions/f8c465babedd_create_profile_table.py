"""create_profile_table

Revision ID: f8c465babedd
Revises: 4c011b536bfd
Create Date: 2026-05-05 14:11:29.061634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8c465babedd'
down_revision: Union[str, Sequence[str], None] = '163bc7506f9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 2. ADD THE TABLE CREATION LOGIC HERE
    op.create_table('profile',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        # ... add your other profile columns here ...
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('profile')

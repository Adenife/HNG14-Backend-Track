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
    op.create_table('profile',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('gender', sa.String(length=255), nullable=False),
        sa.Column('gender_probability', sa.Numeric(precision=128), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('age_group', sa.String(length=255), nullable=False),
        sa.Column('country_id', sa.String(length=255), nullable=False),
        sa.Column('country_name', sa.String(length=255), nullable=True),
        sa.Column('country_probability', sa.Numeric(precision=128), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    # Note: We don't need to add the indexes here because your 
    # next migration (58abf52992b5) is already trying to add them.

def downgrade():
    op.drop_table('profile')

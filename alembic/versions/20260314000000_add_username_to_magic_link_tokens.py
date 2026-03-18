"""Add username column to magic_link_tokens table.

Revision ID: 20260314000000
Revises: 20260204000000
Create Date: 2026-03-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260314000000'
down_revision = '20260204000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'magic_link_tokens',
        sa.Column('username', sa.String(50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('magic_link_tokens', 'username')

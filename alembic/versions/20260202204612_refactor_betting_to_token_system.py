"""Refactor betting to token system.

Revision ID: 20260202204612
Revises: 20260202203021
Create Date: 2026-02-02 20:46:12.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260202204612'
down_revision = '20260202203021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop user_balance table if it exists
    op.execute('DROP TABLE IF EXISTS user_balance')

    # Clear all existing bets (clean slate)
    op.execute('DELETE FROM bets')

    # SQLite doesn't support ALTER TABLE DROP COLUMN, so we need to recreate the table
    # Create temporary table with new schema (without stake and potential_payout)
    op.execute('''
        CREATE TABLE bets_new (
            id VARCHAR NOT NULL,
            user_id VARCHAR NOT NULL,
            match_id VARCHAR NOT NULL,
            league_id VARCHAR NOT NULL,
            outcome VARCHAR NOT NULL,
            odds FLOAT NOT NULL,
            status VARCHAR NOT NULL,
            actual_payout FLOAT,
            created_at DATETIME NOT NULL,
            settled_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE,
            FOREIGN KEY(league_id) REFERENCES leagues (id) ON DELETE CASCADE,
            UNIQUE (user_id, match_id, league_id)
        )
    ''')

    # Copy data from old table to new table
    op.execute('''
        INSERT INTO bets_new (id, user_id, match_id, league_id, outcome, odds, status, actual_payout, created_at, settled_at)
        SELECT id, user_id, match_id, league_id, outcome, odds, status, actual_payout, created_at, settled_at
        FROM bets
    ''')

    # Drop old table
    op.drop_table('bets')

    # Rename new table
    op.execute('ALTER TABLE bets_new RENAME TO bets')


def downgrade() -> None:
    # This downgrade is complex because SQLite doesn't support dropping columns easily
    # We would need to recreate the table again with the old schema
    # For now, we'll create a simple placeholder that adds back the columns with defaults

    # Clear bets table
    op.execute('DELETE FROM bets')

    # Create new bets table with old schema
    op.execute('''
        CREATE TABLE bets_old (
            id VARCHAR NOT NULL,
            user_id VARCHAR NOT NULL,
            match_id VARCHAR NOT NULL,
            league_id VARCHAR NOT NULL,
            outcome VARCHAR NOT NULL,
            stake FLOAT NOT NULL DEFAULT 0.0,
            odds FLOAT NOT NULL,
            potential_payout FLOAT NOT NULL DEFAULT 0.0,
            status VARCHAR NOT NULL,
            actual_payout FLOAT,
            created_at DATETIME NOT NULL,
            settled_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE,
            FOREIGN KEY(league_id) REFERENCES leagues (id) ON DELETE CASCADE
        )
    ''')

    # Copy data from current table to old table
    op.execute('''
        INSERT INTO bets_old (id, user_id, match_id, league_id, outcome, stake, odds, potential_payout, status, actual_payout, created_at, settled_at)
        SELECT id, user_id, match_id, league_id, outcome, 0.0, odds, 0.0, status, actual_payout, created_at, settled_at
        FROM bets
    ''')

    # Drop current table
    op.drop_table('bets')

    # Rename old table
    op.execute('ALTER TABLE bets_old RENAME TO bets')

    # Recreate user_balance table
    op.create_table(
        'user_balance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False, server_default='1000.0'),
        sa.Column('total_wagered', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_winnings', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

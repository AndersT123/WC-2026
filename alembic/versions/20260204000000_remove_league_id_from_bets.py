"""Remove league_id from bets table - bets now apply to all leagues.

Revision ID: 20260204000000
Revises: 20260202204612
Create Date: 2026-02-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260204000000'
down_revision = '20260202204612'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite doesn't support ALTER TABLE DROP COLUMN, so we need to recreate the table
    # Create temporary table without league_id
    op.execute('''
        CREATE TABLE bets_new (
            id VARCHAR NOT NULL,
            user_id VARCHAR NOT NULL,
            match_id VARCHAR NOT NULL,
            outcome VARCHAR NOT NULL,
            odds FLOAT NOT NULL,
            status VARCHAR NOT NULL,
            actual_payout FLOAT,
            created_at DATETIME NOT NULL,
            settled_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE,
            UNIQUE (user_id, match_id)
        )
    ''')

    # Copy data from old table to new table, keeping the most recent bet for each user/match combination
    op.execute('''
        INSERT INTO bets_new (id, user_id, match_id, outcome, odds, status, actual_payout, created_at, settled_at)
        SELECT id, user_id, match_id, outcome, odds, status, actual_payout, created_at, settled_at
        FROM bets
        WHERE (user_id, match_id, created_at) IN (
            SELECT user_id, match_id, MAX(created_at)
            FROM bets
            GROUP BY user_id, match_id
        )
    ''')

    # Drop old table
    op.drop_table('bets')

    # Rename new table
    op.execute('ALTER TABLE bets_new RENAME TO bets')


def downgrade() -> None:
    # Downgrade: recreate table with league_id
    op.execute('''
        CREATE TABLE bets_old (
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

    # Copy data back, using a default league_id (first league for each user)
    op.execute('''
        INSERT INTO bets_old (id, user_id, match_id, league_id, outcome, odds, status, actual_payout, created_at, settled_at)
        SELECT b.id, b.user_id, b.match_id,
               (SELECT id FROM leagues WHERE creator_id = b.user_id LIMIT 1),
               b.outcome, b.odds, b.status, b.actual_payout, b.created_at, b.settled_at
        FROM bets b
    ''')

    # Drop current table
    op.drop_table('bets')

    # Rename old table
    op.execute('ALTER TABLE bets_old RENAME TO bets')

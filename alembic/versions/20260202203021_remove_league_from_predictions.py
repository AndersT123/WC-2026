"""Remove league_id from predictions table.

Revision ID: 20260202203021
Revises: b05a7fe5cb8c
Create Date: 2026-02-02 20:30:21.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260202203021"
down_revision: Union[str, None] = "b05a7fe5cb8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade: Remove league_id from predictions, deduplicating by keeping most recent."""
    # Create backup table to log which predictions were deduplicated
    op.create_table(
        "predictions_backup",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("league_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.Column("points_earned", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create new predictions table without league_id
    op.create_table(
        "predictions_new",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "match_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.Column("points_earned", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "match_id", name="uq_prediction"),
        sa.CheckConstraint("home_score >= 0", name="ck_home_score_non_negative"),
        sa.CheckConstraint("away_score >= 0", name="ck_away_score_non_negative"),
    )

    # Add indexes
    op.create_index("idx_user_id_predictions_new", "predictions_new", ["user_id"])
    op.create_index("idx_match_id_predictions_new", "predictions_new", ["match_id"])
    op.create_index(
        "idx_user_match",
        "predictions_new",
        ["user_id", "match_id"],
    )

    # Copy deduplicated predictions from old table to new table
    # Keep the most recent prediction (by updated_at) for each (user_id, match_id)
    op.execute(
        """
        INSERT INTO predictions_new (id, user_id, match_id, home_score, away_score, points_earned, created_at, updated_at)
        SELECT DISTINCT ON (user_id, match_id) id, user_id, match_id, home_score, away_score, points_earned, created_at, updated_at
        FROM predictions
        ORDER BY user_id, match_id, updated_at DESC
        """
    )

    # Copy duplicates to backup table for reference
    op.execute(
        """
        INSERT INTO predictions_backup (id, user_id, match_id, league_id, home_score, away_score, points_earned, created_at, updated_at)
        SELECT id, user_id, match_id, league_id, home_score, away_score, points_earned, created_at, updated_at
        FROM predictions
        WHERE (user_id, match_id, updated_at) NOT IN (
            SELECT user_id, match_id, updated_at FROM predictions_new
        )
        """
    )

    # Drop old table
    op.drop_table("predictions")

    # Rename new table to predictions
    op.rename_table("predictions_new", "predictions")


def downgrade() -> None:
    """Downgrade: Restore league_id to predictions.

    WARNING: This operation will duplicate predictions across all user's leagues.
    The original league-specific predictions cannot be restored from deduplication.
    """
    # Create new predictions table with league_id
    op.create_table(
        "predictions_new",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "match_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "league_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leagues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.Column("points_earned", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "match_id", "league_id", name="uq_prediction"),
        sa.CheckConstraint("home_score >= 0", name="ck_home_score_non_negative"),
        sa.CheckConstraint("away_score >= 0", name="ck_away_score_non_negative"),
    )

    # Add indexes
    op.create_index("idx_user_id_predictions_new", "predictions_new", ["user_id"])
    op.create_index("idx_match_id_predictions_new", "predictions_new", ["match_id"])
    op.create_index(
        "idx_match_league",
        "predictions_new",
        ["match_id", "league_id"],
    )
    op.create_index(
        "idx_league_points",
        "predictions_new",
        ["league_id", "points_earned"],
    )

    # Replicate predictions from old table to new table for all user's leagues
    op.execute(
        """
        INSERT INTO predictions_new (id, user_id, match_id, league_id, home_score, away_score, points_earned, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            p.user_id,
            p.match_id,
            lm.league_id,
            p.home_score,
            p.away_score,
            p.points_earned,
            p.created_at,
            p.updated_at
        FROM predictions p
        CROSS JOIN league_memberships lm
        WHERE lm.user_id = p.user_id
        """
    )

    # Drop old table
    op.drop_table("predictions")

    # Rename new table to predictions
    op.rename_table("predictions_new", "predictions")

    # Drop backup table if it exists
    op.execute("DROP TABLE IF EXISTS predictions_backup")

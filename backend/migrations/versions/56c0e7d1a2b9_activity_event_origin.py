"""Distinguish local demo activity from live user activity."""

from alembic import op
import sqlalchemy as sa


revision = "56c0e7d1a2b9"
down_revision = "2a19d7c8e401"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activity_events",
        sa.Column("origin", sa.String(), nullable=False, server_default="live"),
    )


def downgrade() -> None:
    op.drop_column("activity_events", "origin")

"""Persist low-sensitivity business activity events for analytics."""

from alembic import op
import sqlalchemy as sa


revision = "2a19d7c8e401"
down_revision = "9df2b9f5a4c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=True),
        sa.Column("actor_role", sa.String(), nullable=False, server_default="guest"),
        sa.Column("subject_type", sa.String(), nullable=True),
        sa.Column("subject_id", sa.String(), nullable=True),
        sa.Column("application_method", sa.String(), nullable=False, server_default="none"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_events_event_type", "activity_events", ["event_type"])
    op.create_index("ix_activity_events_occurred_at", "activity_events", ["occurred_at"])
    op.create_index("ix_activity_events_actor_user_id", "activity_events", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_activity_events_actor_user_id", table_name="activity_events")
    op.drop_index("ix_activity_events_occurred_at", table_name="activity_events")
    op.drop_index("ix_activity_events_event_type", table_name="activity_events")
    op.drop_table("activity_events")

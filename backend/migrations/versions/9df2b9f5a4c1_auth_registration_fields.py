"""Add user registration and token version fields.

Revision ID: 9df2b9f5a4c1
Revises: 40f369b690d5
Create Date: 2026-11-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9df2b9f5a4c1"
down_revision: Union[str, Sequence[str], None] = "40f369b690d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(), nullable=False, server_default=""))
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"))
    op.execute("UPDATE users SET name = 'Demo Candidate' WHERE email = 'candidate@example.com' AND name = ''")
    op.execute("UPDATE users SET name = 'Demo Recruiter' WHERE email = 'recruiter@example.com' AND name = ''")
    op.execute("UPDATE users SET name = 'Demo Admin' WHERE email = 'admin@example.com' AND name = ''")


def downgrade() -> None:
    op.drop_column("users", "auth_version")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "name")

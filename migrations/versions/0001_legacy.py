"""Baseline matching the original PostgreSQL schema; existing installs stamp 0001."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.Text, unique=True),
        sa.Column("password", sa.Text),
        sa.Column("is_verified", sa.Integer, server_default="0"),
        sa.Column("role", sa.Text, server_default="user"),
    )
    op.create_table(
        "progress",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.Text),
        sa.Column("weight", sa.Float),
        sa.Column("calories", sa.Integer),
    )


def downgrade():
    raise RuntimeError("Destructive downgrade disabled; restore a verified backup")

"""Retain optional owner-scoped request identities for retry-safe progress saves."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("progress", sa.Column("request_key", sa.String(36), nullable=True))
    op.create_index("uq_progress_email_request_key", "progress", ["email", "request_key"], unique=True)


def downgrade():
    op.drop_index("uq_progress_email_request_key", table_name="progress")
    op.drop_column("progress", "request_key")

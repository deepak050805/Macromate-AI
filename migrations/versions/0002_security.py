"""Harden accounts and progress while retaining legacy undated records."""
from alembic import op
import sqlalchemy as sa
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    duplicates = connection.execute(sa.text("SELECT lower(trim(email)) FROM users GROUP BY lower(trim(email)) HAVING count(*) > 1")).first()
    if duplicates:
        raise RuntimeError("Resolve duplicate normalized account emails before migrating")
    connection.execute(sa.text("UPDATE progress SET email=lower(trim(email))"))
    connection.execute(sa.text("UPDATE users SET email=lower(trim(email))"))
    connection.execute(sa.text("UPDATE users SET password='!reset-required' WHERE password IS NULL OR (password NOT LIKE 'scrypt:%' AND password NOT LIKE 'pbkdf2:%')"))
    connection.execute(sa.text("UPDATE users SET is_verified=0 WHERE is_verified IS NULL"))
    connection.execute(sa.text("UPDATE users SET role='user' WHERE role IS NULL"))
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("auth_version", sa.Integer, nullable=False, server_default="1"))
        batch.add_column(sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch.alter_column("email", existing_type=sa.Text, nullable=False)
        batch.alter_column("password", existing_type=sa.Text, nullable=False)
        batch.alter_column("is_verified", existing_type=sa.Integer, nullable=False)
        batch.alter_column("role", existing_type=sa.Text, nullable=False)
    with op.batch_alter_table("progress") as batch:
        batch.add_column(sa.Column("record_date", sa.Date, nullable=True))
        batch.add_column(sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch.alter_column("email", existing_type=sa.Text, nullable=False)
        batch.alter_column("weight", existing_type=sa.Float, nullable=False)
        batch.alter_column("calories", existing_type=sa.Integer, nullable=False)
        batch.create_foreign_key("fk_progress_user_email", "users", ["email"], ["email"])
        batch.create_check_constraint("ck_progress_weight", "weight > 0 AND weight <= 500")
        batch.create_check_constraint("ck_progress_calories", "calories >= 0 AND calories <= 20000")
        batch.create_index("ix_progress_email_date", ["email", "record_date", "id"])
    op.create_table("otp_challenges", sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True), sa.Column("digest", sa.String(64), nullable=False), sa.Column("purpose", sa.String(12), nullable=False), sa.Column("expires_at", sa.Float, nullable=False), sa.Column("sent_at", sa.Float, nullable=False), sa.Column("attempts", sa.Integer, nullable=False))


def downgrade():
    raise RuntimeError("Security downgrade disabled; restore a verified backup")

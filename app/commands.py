"""Explicit operator actions; registering commands performs no database work."""

from time import time

import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Otp, User
from app.repositories.users import by_email
from app.utils.validation import ValidationError, email_value


@click.group("accounts")
def accounts():
    """Manage existing accounts with configured database operator access."""


@accounts.command("promote")
@click.option("--email", required=True, help="Email of an existing verified account.")
@click.confirmation_option(prompt="Grant administrator access and revoke existing sessions?")
@with_appcontext
def promote(email):
    """Grant administrator access; never create or verify an account."""
    try:
        email = email_value(email)
    except ValidationError as error:
        raise click.ClickException(str(error)) from None
    try:
        user = by_email(email, lock=True)
        if user is None:
            raise click.ClickException("Account not found")
        if not user.is_verified:
            raise click.ClickException("Verify the account by email before granting administrator access")
        if user.role == "admin":
            click.echo("Account already has administrator access; no changes made.")
            return
        user.role = "admin"
        user.auth_version += 1
        user_id = user.id
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("account_promotion_failed")
        raise click.ClickException("Promotion failed; inspect account state before retrying") from None
    current_app.logger.info("account_promoted user_id=%s", user_id)
    click.echo("Administrator access granted; existing sessions revoked.")


@click.group("otp")
def otp():
    """Maintain verification challenges with configured database operator access."""


@otp.command("cleanup")
@click.option("--limit", type=click.IntRange(1, 10000), default=1000, show_default=True, help="Maximum expired challenges to consider.")
@click.option("--apply", "apply_changes", is_flag=True, help="Delete expired challenges instead of reporting a dry run.")
@click.option("--yes", is_flag=True, help="Skip the confirmation required with --apply.")
@with_appcontext
def cleanup(limit, apply_changes, yes):
    """Inspect expired challenges; deletion requires --apply and confirmation."""
    if apply_changes and not yes:
        click.confirm("Delete the selected expired verification challenges?", default=False, abort=True)
    cutoff = time()
    candidates = (
        db.select(User.id)
        .join(Otp, Otp.user_id == User.id)
        .where(Otp.expires_at <= cutoff)
        .order_by(Otp.expires_at, User.id)
        .limit(limit)
    )
    try:
        if not apply_changes:
            count = len(db.session.scalars(candidates).all())
            db.session.rollback()
            click.echo(f"Dry run: {count} expired challenge(s) eligible, limited to {limit}. No changes made.")
            return
        # Issue and confirmation also lock User rows. PostgreSQL skips accounts
        # that are currently using their challenge instead of waiting on them.
        user_ids = db.session.scalars(candidates.with_for_update(of=User, skip_locked=True)).all()
        count = 0
        if user_ids:
            # Recheck expiry in a fresh statement after acquiring account locks;
            # a challenge renewed after the candidate snapshot must survive.
            result = db.session.execute(
                db.delete(Otp).where(Otp.user_id.in_(user_ids), Otp.expires_at <= cutoff).execution_options(synchronize_session=False)
            )
            count = result.rowcount
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.error("otp_cleanup_failed")
        raise click.ClickException("OTP cleanup failed; inspect challenge state before retrying") from None
    current_app.logger.info("otp_cleanup_completed count=%s", count)
    click.echo(f"Deleted {count} expired challenge(s).")


def register_commands(app):
    app.cli.add_command(accounts)
    app.cli.add_command(otp)

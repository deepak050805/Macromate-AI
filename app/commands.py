"""Explicit operator actions; registering commands performs no database work."""

import click
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
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


def register_commands(app):
    app.cli.add_command(accounts)

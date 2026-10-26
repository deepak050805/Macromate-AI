"""Retention batches must respect real PostgreSQL account-row contention."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from flask_migrate import upgrade
from sqlalchemy import text

from app.extensions import db
from app.models import Otp, User
from app.repositories.users import by_id
from app.services.otp import issue


@pytest.fixture
def retention_accounts(postgres_app_factory, monkeypatch):
    monkeypatch.setattr("app.commands.time", lambda: 1000.0)
    sent = []
    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: sent.append((email, code)))
    observer = postgres_app_factory()
    identifiers = {}
    with observer.app_context():
        upgrade()
        for label, expires_at, attempts in [
            ("locked-expired", 100.0, 0),
            ("unlocked-expired", 200.0, 0),
            ("active", 2000.0, 0),
            ("active-exhausted", 3000.0, 5),
        ]:
            user = User(email=f"{label}@example.test", password="!fixture-no-login", is_verified=1)
            db.session.add(user)
            db.session.flush()
            db.session.add(Otp(user_id=user.id, digest="0" * 64, purpose="reset", expires_at=expires_at, sent_at=0.0, attempts=attempts))
            identifiers[label] = user.id
        db.session.commit()
    return observer, identifiers, sent


def invoke_cleanup(app, *arguments):
    """Bound lock waits/statements independently of the Python future deadline."""
    with app.app_context():
        db.session.execute(text("SET LOCAL lock_timeout = '2s'"))
        db.session.execute(text("SET LOCAL statement_timeout = '5s'"))
        result = app.test_cli_runner().invoke(args=["otp", "cleanup", *arguments])
        return result.exit_code, result.output


def challenge_ids(app):
    with app.app_context():
        return set(db.session.scalars(db.select(Otp.user_id)).all())


def test_cleanup_skips_a_locked_account_and_fills_the_batch_with_unlocked_expiry(
    postgres_app_factory, retention_accounts
):
    observer, identifiers, sent = retention_accounts
    actor = postgres_app_factory()
    with observer.app_context():
        engine = db.engine
    with ThreadPoolExecutor(max_workers=1) as executor:
        with engine.begin() as holder:
            holder.execute(text("SELECT id FROM users WHERE id = :id FOR UPDATE"), {"id": identifiers["locked-expired"]}).one()
            future = executor.submit(invoke_cleanup, actor, "--apply", "--yes", "--limit", "1")
            status, output = future.result(timeout=10)
            assert status == 0, output
            assert "Deleted 1 expired" in output
            # Completion while this transaction still owns its lock proves that
            # the batch skipped contention instead of waiting for its release.
            assert holder.in_transaction()
            assert challenge_ids(observer) == {
                identifiers["locked-expired"], identifiers["active"], identifiers["active-exhausted"],
            }
    assert sent == []


def test_dry_run_can_count_expired_challenges_while_an_account_is_locked(
    postgres_app_factory, retention_accounts
):
    observer, identifiers, sent = retention_accounts
    actor = postgres_app_factory()
    with observer.app_context():
        engine = db.engine
    with ThreadPoolExecutor(max_workers=1) as executor:
        with engine.begin() as holder:
            holder.execute(text("SELECT id FROM users WHERE id = :id FOR UPDATE"), {"id": identifiers["locked-expired"]}).one()
            future = executor.submit(invoke_cleanup, actor)
            status, output = future.result(timeout=10)
            assert status == 0, output
            assert "Dry run: 2 expired" in output
            assert holder.in_transaction()
            assert challenge_ids(observer) == set(identifiers.values())
    assert sent == []


def test_cleanup_preserves_a_challenge_being_renewed_and_after_renewal_commits(
    postgres_app_factory, retention_accounts
):
    observer, identifiers, sent = retention_accounts
    issuer, actor = postgres_app_factory(), postgres_app_factory()
    renewed_id = identifiers["locked-expired"]
    with ThreadPoolExecutor(max_workers=1) as executor:
        with issuer.app_context():
            db.session.execute(text("SET LOCAL lock_timeout = '2s'"))
            db.session.execute(text("SET LOCAL statement_timeout = '5s'"))
            user = by_id(renewed_id, lock=True)
            assert issue(user, "reset") is True
            db.session.flush()
            renewed_expiry = db.session.get(Otp, renewed_id).expires_at
            assert renewed_expiry > 1000.0
            future = executor.submit(invoke_cleanup, actor, "--apply", "--yes")
            status, output = future.result(timeout=10)
            assert status == 0, output
            assert "Deleted 1 expired" in output
            db.session.commit()
    assert len(sent) == 1
    assert challenge_ids(observer) == {renewed_id, identifiers["active"], identifiers["active-exhausted"]}
    status, output = invoke_cleanup(actor, "--apply", "--yes")
    assert status == 0, output
    assert "Deleted 0 expired" in output
    with observer.app_context():
        challenge = db.session.get(Otp, renewed_id)
        assert challenge.expires_at == renewed_expiry
        assert challenge.attempts == 0
        assert challenge.purpose == "reset"

"""Operator retention cleanup must be explicit, bounded and safe for live codes."""

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.dml import Delete

from app.extensions import db
from app.models import Otp, User


@pytest.fixture
def challenges(app, monkeypatch):
    monkeypatch.setattr("app.commands.time", lambda: 1000.0)
    identifiers = {}
    for label, expiry, attempts in [
        ("oldest", 100.0, 0),
        ("expired", 200.0, 5),
        ("boundary", 1000.0, 0),
        ("active", 1001.0, 0),
        ("active-exhausted", 2000.0, 5),
    ]:
        user = User(email=f"{label}@example.test", password="!fixture-no-login", is_verified=1)
        db.session.add(user)
        db.session.flush()
        db.session.add(Otp(user_id=user.id, digest="0" * 64, purpose="reset", expires_at=expiry, sent_at=0.0, attempts=attempts))
        identifiers[label] = user.id
    db.session.commit()
    return identifiers


def remaining_ids():
    return set(db.session.scalars(db.select(Otp.user_id)).all())


def cleanup(app, *arguments, **kwargs):
    return app.test_cli_runner().invoke(args=["otp", "cleanup", *arguments], **kwargs)


def test_cleanup_defaults_to_a_dry_run_without_confirmation(app, challenges):
    result = cleanup(app)
    assert result.exit_code == 0
    assert "Dry run: 3 expired" in result.output
    assert "No changes made" in result.output
    assert "[y/N]" not in result.output
    assert remaining_ids() == set(challenges.values())


def test_yes_flag_alone_cannot_turn_a_dry_run_into_deletion(app, challenges):
    result = cleanup(app, "--yes")
    assert result.exit_code == 0
    assert "Dry run:" in result.output
    assert remaining_ids() == set(challenges.values())


def test_dry_run_and_apply_obey_the_same_batch_limit(app, challenges):
    dry_run = cleanup(app, "--limit", "2")
    assert "Dry run: 2 expired" in dry_run.output
    result = cleanup(app, "--apply", "--yes", "--limit", "2")
    assert result.exit_code == 0
    assert "Deleted 2 expired" in result.output
    assert remaining_ids() == {challenges["boundary"], challenges["active"], challenges["active-exhausted"]}


def test_apply_preserves_all_unexpired_challenges_even_when_attempts_are_exhausted(app, challenges):
    result = cleanup(app, "--apply", "--yes")
    assert result.exit_code == 0
    assert "Deleted 3 expired" in result.output
    assert remaining_ids() == {challenges["active"], challenges["active-exhausted"]}
    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == len(challenges)


def test_declining_apply_confirmation_never_changes_rows(app, challenges):
    result = cleanup(app, "--apply", input="n\n")
    assert result.exit_code != 0
    assert remaining_ids() == set(challenges.values())


def test_interactive_confirmation_can_authorize_deletion(app, challenges):
    result = cleanup(app, "--apply", input="y\n")
    assert result.exit_code == 0
    assert remaining_ids() == {challenges["active"], challenges["active-exhausted"]}


@pytest.mark.parametrize("limit", ["0", "10001", "not-a-number"])
def test_invalid_batch_limits_never_run_cleanup(app, challenges, limit):
    result = cleanup(app, "--apply", "--yes", "--limit", limit)
    assert result.exit_code != 0
    assert remaining_ids() == set(challenges.values())


def test_failed_commit_rolls_back_deleted_rows_and_hides_diagnostics(app, challenges, monkeypatch, caplog):
    with monkeypatch.context() as outage:
        outage.setattr(db.session, "commit", Mock(side_effect=SQLAlchemyError("private-otp-cleanup-diagnostic")))
        result = cleanup(app, "--apply", "--yes")
    assert result.exit_code != 0
    assert "inspect challenge state" in result.output
    assert "private-otp-cleanup-diagnostic" not in result.output + caplog.text
    assert remaining_ids() == set(challenges.values())


def test_cleanup_rechecks_expiry_after_selecting_and_locking_candidates(app, challenges, monkeypatch):
    original_execute = db.session.execute
    renewed = challenges["oldest"]

    def renew_before_delete(statement, *args, **kwargs):
        if isinstance(statement, Delete):
            original_execute(db.update(Otp).where(Otp.user_id == renewed).values(expires_at=2000.0))
        return original_execute(statement, *args, **kwargs)

    monkeypatch.setattr(db.session, "execute", renew_before_delete)
    result = cleanup(app, "--apply", "--yes")
    assert result.exit_code == 0
    assert "Deleted 2 expired" in result.output
    assert remaining_ids() == {renewed, challenges["active"], challenges["active-exhausted"]}


def test_cleanup_uses_one_fixed_time_cutoff_for_the_entire_batch(app, challenges, monkeypatch):
    clock = Mock(side_effect=[1000.0, 9000.0])
    monkeypatch.setattr("app.commands.time", clock)
    result = cleanup(app, "--apply", "--yes")
    assert result.exit_code == 0
    assert clock.call_count == 1
    assert remaining_ids() == {challenges["active"], challenges["active-exhausted"]}

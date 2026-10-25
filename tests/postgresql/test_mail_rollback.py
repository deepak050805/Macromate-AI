import time

from flask_migrate import upgrade

from app.extensions import db
from app.models import Otp, User
from app.services.mail import DeliveryError
from app.services.otp import digest, issue
from app.services.passwords import hash_password


def fail_delivery(*args):
    raise DeliveryError("private-provider-diagnostic")


def test_failed_signup_is_not_persisted_and_another_app_can_retry(
    postgres_app_factory, monkeypatch
):
    app = postgres_app_factory()
    other = postgres_app_factory()
    with app.app_context():
        upgrade()
    payload = {"email": "owner@example.test", "password": "fictional owner password"}
    monkeypatch.setattr("app.services.otp.send_code", fail_delivery)
    result = app.test_client().post("/api/auth/signup", json=payload)
    assert result.status_code == 503
    assert result.json["error"] == "mail_unavailable"
    with other.app_context():
        assert db.session.scalar(db.select(User)) is None
        assert db.session.scalar(db.select(Otp)) is None

    sent = []
    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: sent.append(code))
    assert other.test_client().post("/api/auth/signup", json=payload).status_code == 202
    assert len(sent) == 1
    assert (
        app.test_client().post("/api/auth/verify-otp", json={**payload, "otp": sent[0]}).status_code
        == 200
    )


def test_failed_reset_preserves_committed_challenge_across_applications(
    postgres_app_factory, monkeypatch
):
    app = postgres_app_factory()
    other = postgres_app_factory()
    sent = []
    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: sent.append(code))
    with app.app_context():
        upgrade()
        user = User(
            email="owner@example.test",
            password=hash_password("fictional original password"),
            is_verified=1,
        )
        db.session.add(user)
        db.session.flush()
        issue(user, "reset")
        row = db.session.get(Otp, user.id)
        row.sent_at = time.time() - 120
        row.attempts = 2
        db.session.commit()
        user_id = user.id
        credentials = (user.password, user.auth_version, user.is_verified)
        snapshot = (row.digest, row.purpose, row.sent_at, row.expires_at, row.attempts)

    monkeypatch.setattr("app.services.otp.send_code", fail_delivery)
    payload = {"email": "owner@example.test"}
    assert other.test_client().post("/api/auth/request-reset", json=payload).status_code == 503
    with app.app_context():
        row = db.session.get(Otp, user_id)
        assert (
            row.digest,
            row.purpose,
            row.sent_at,
            row.expires_at,
            row.attempts,
        ) == snapshot
        assert row.digest == digest(user_id, "reset", sent[0])
        user = db.session.get(User, user_id)
        assert (user.password, user.auth_version, user.is_verified) == credentials

    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: sent.append(code))
    assert other.test_client().post("/api/auth/request-reset", json=payload).status_code == 202
    assert len(sent) == 2
    result = app.test_client().post(
        "/api/auth/reset-password",
        json={**payload, "otp": sent[-1], "password": "fictional replacement password"},
    )
    assert result.status_code == 200
    with other.app_context():
        assert db.session.get(Otp, user_id) is None
        assert db.session.get(User, user_id).auth_version == credentials[1] + 1

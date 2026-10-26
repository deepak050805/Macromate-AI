from app.extensions import db
from app.models import Otp
from app.services.otp import issue
from app.services.passwords import verify_password


def test_legacy_recovery(logged_in, account, monkeypatch):
    sent = []
    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: sent.append(code))
    account.password = "!reset-required"
    db.session.commit()
    old_version = account.auth_version
    assert (
        logged_in.post("/api/auth/request-reset", json={"email": account.email}).status_code == 202
    )
    response = logged_in.post(
        "/api/auth/reset-password",
        json={"email": account.email, "otp": sent[0], "password": "brand new secure password"},
    )
    assert response.status_code == 200
    assert verify_password(account.password, "brand new secure password")
    assert account.auth_version == old_version + 1
    assert logged_in.get("/api/tracker/history").status_code == 401
    assert (
        logged_in.post(
            "/api/auth/reset-password",
            json={"email": account.email, "otp": sent[0], "password": "brand new secure password"},
        ).status_code
        == 400
    )


def test_unknown_reset(client):
    assert (
        client.post("/api/auth/request-reset", json={"email": "unknown@example.test"}).status_code
        == 202
    )


def test_failed_reset_commit_preserves_session_password_and_challenge(logged_in, account, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    from unittest.mock import Mock

    codes = []
    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: codes.append(code))
    issue(account, "reset")
    db.session.commit()
    user_id, old_version = account.id, account.auth_version
    with monkeypatch.context() as outage:
        outage.setattr(db.session, "commit", Mock(side_effect=SQLAlchemyError("private-reset-error")))
        response = logged_in.post("/api/auth/reset-password", json={
            "email": account.email, "otp": codes[0], "password": "replacement recovery password",
        })
    assert response.status_code == 503
    assert "private-reset-error" not in response.text
    db.session.refresh(account)
    assert account.auth_version == old_version
    assert verify_password(account.password, "correct horse battery")
    assert db.session.get(Otp, user_id) is not None
    assert logged_in.get("/api/tracker/history").status_code == 200

from unittest.mock import Mock

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.services.passwords import verify_password


def test_password_change_requires_current_password_and_revokes_sessions(logged_in, account, app):
    other = app.test_client()
    with other.session_transaction() as session:
        session["user_id"] = account.id
        session["auth_version"] = account.auth_version
    response = logged_in.post("/api/auth/change-password", json={
        "current_password": "correct horse battery", "password": "new correct horse battery",
    })
    assert response.status_code == 200
    assert logged_in.get("/api/tracker/history").status_code == 401
    assert other.get("/api/tracker/history").status_code == 401
    assert logged_in.post("/api/auth/login", json={
        "email": account.email, "password": "correct horse battery",
    }).status_code == 401
    assert logged_in.post("/api/auth/login", json={
        "email": account.email, "password": "new correct horse battery",
    }).status_code == 200


def test_wrong_current_password_does_not_change_credentials(logged_in, account):
    version = account.auth_version
    response = logged_in.post("/api/auth/change-password", json={
        "current_password": "incorrect password", "password": "new correct horse battery",
    })
    assert response.status_code == 400
    db.session.refresh(account)
    assert account.auth_version == version
    assert verify_password(account.password, "correct horse battery")


def test_invalid_new_password_is_rejected_before_mutation(logged_in, account):
    response = logged_in.post("/api/auth/change-password", json={
        "current_password": "correct horse battery", "password": "short",
    })
    assert response.status_code == 400
    assert verify_password(account.password, "correct horse battery")


def test_anonymous_password_change_is_forbidden(client):
    assert client.post("/api/auth/change-password", json={}).status_code == 401


def test_failed_password_commit_preserves_old_credentials_and_current_session(logged_in, account, monkeypatch, caplog):
    with monkeypatch.context() as outage:
        outage.setattr(db.session, "commit", Mock(side_effect=SQLAlchemyError("private-commit-diagnostic")))
        response = logged_in.post("/api/auth/change-password", json={
            "current_password": "correct horse battery", "password": "replacement fixture password",
        })
    assert response.status_code == 503
    assert "private-commit-diagnostic" not in response.text
    assert "private-commit-diagnostic" not in caplog.text
    db.session.refresh(account)
    assert verify_password(account.password, "correct horse battery")
    assert logged_in.get("/api/tracker/history").status_code == 200

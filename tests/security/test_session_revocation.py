from app.extensions import db


def test_global_sign_out_revokes_sessions_without_replacing_the_password(logged_in, account, app):
    original_hash = account.password
    other = app.test_client()
    with other.session_transaction() as session:
        session["user_id"] = account.id
        session["auth_version"] = account.auth_version
    response = logged_in.post("/api/auth/revoke-sessions", json={"current_password": "correct horse battery"})
    assert response.status_code == 200
    db.session.refresh(account)
    assert account.password == original_hash
    assert logged_in.get("/api/tracker/history").status_code == 401
    assert other.get("/api/tracker/history").status_code == 401
    assert logged_in.post("/api/auth/login", json={
        "email": account.email, "password": "correct horse battery",
    }).status_code == 200


def test_global_sign_out_requires_current_password(logged_in, account):
    version = account.auth_version
    assert logged_in.post("/api/auth/revoke-sessions", json={"current_password": "wrong"}).status_code == 400
    db.session.refresh(account)
    assert account.auth_version == version
    assert logged_in.get("/api/tracker/history").status_code == 200


def test_anonymous_global_sign_out_is_forbidden(client):
    assert client.post("/api/auth/revoke-sessions", json={}).status_code == 401

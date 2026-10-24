from app.extensions import db


def test_login_logout(client, account):
    with client.session_transaction() as session:
        session["stale"] = "discard"
    response = client.post(
        "/api/auth/login", json={"email": account.email, "password": "correct horse battery"}
    )
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "stale" not in session
        assert session["user_id"] == account.id
    assert client.get("/api/tracker/history").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/tracker/history").status_code == 401


def test_revoked_session(logged_in, account):
    account.auth_version += 1
    db.session.commit()
    assert logged_in.get("/api/tracker/history").status_code == 401


def test_unverified_session(logged_in, account):
    account.is_verified = 0
    db.session.commit()
    assert logged_in.get("/api/tracker/history").status_code == 401

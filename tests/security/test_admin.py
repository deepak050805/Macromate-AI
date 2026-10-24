from app.extensions import db


def test_admin_access(client, logged_in, account):
    assert logged_in.get("/api/auth/all-users").status_code == 403
    account.role = "admin"
    db.session.commit()
    response = logged_in.get("/api/auth/all-users")
    assert response.status_code == 200
    assert set(response.json["users"][0]) == {"id", "email", "verified"}
    account.role = "user"
    db.session.commit()
    assert logged_in.get("/api/auth/all-users").status_code == 403

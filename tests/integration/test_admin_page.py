from app.extensions import db


def test_admin_page(logged_in, account):
    assert logged_in.get("/admin").status_code == 403
    account.role = "admin"
    db.session.commit()
    response = logged_in.get("/admin")
    assert response.status_code == 200
    assert 'id="users-rows"' in response.text
    assert logged_in.get("/static/js/admin.js").status_code == 200

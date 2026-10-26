from app.extensions import db
from app.models import User


def test_json_surrogate_password_is_a_validation_error_not_server_failure(client):
    response = client.post("/api/auth/signup", json={
        "email": "encoding@example.test", "password": "long password \ud800",
    })
    assert response.status_code == 400
    assert response.json["error"] == "validation_error"
    assert db.session.scalar(db.select(db.func.count(User.id))) == 0

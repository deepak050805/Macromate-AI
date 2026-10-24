from datetime import date

from app.extensions import db
from app.models import Progress, User


def test_cross_user(logged_in):
    other = User(email="other@example.test", password="!reset-required", is_verified=1)
    db.session.add(other)
    db.session.flush()
    record = Progress(email=other.email, weight=70, calories=2000, record_date=date(2024, 1, 1))
    db.session.add(record)
    db.session.commit()
    assert logged_in.get("/api/tracker/history").json["records"] == []
    assert logged_in.get(f"/api/tracker/get/{other.email}").status_code == 403
    assert (
        logged_in.put(
            f"/api/tracker/{record.id}", json={"weight": 71, "calories": 2000, "date": "2024-01-01"}
        ).status_code
        == 404
    )
    assert logged_in.delete(f"/api/tracker/{record.id}").status_code == 404
    assert db.session.get(Progress, record.id) is not None


def test_anonymous(client):
    assert client.post("/api/tracker/add", json={}).status_code == 401
    assert client.get("/api/tracker/get/any@example.test").status_code == 401

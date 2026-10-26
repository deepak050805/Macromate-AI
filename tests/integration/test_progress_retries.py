from uuid import uuid4

from app.extensions import db
from app.models import Progress, User


def entry():
    return {"date": "2024-01-01", "weight": 70, "calories": 2000, "request_key": str(uuid4())}


def test_repeated_create_returns_the_same_owned_record(logged_in):
    body = entry()
    first = logged_in.post("/api/tracker/add", json=body)
    again = logged_in.post("/api/tracker/add", json=body)
    assert first.status_code == again.status_code == 201
    assert first.json == again.json
    assert db.session.scalar(db.select(db.func.count(Progress.id))) == 1


def test_reusing_a_key_with_different_fields_does_not_mutate_or_duplicate(logged_in):
    body = entry()
    logged_in.post("/api/tracker/add", json=body)
    response = logged_in.post("/api/tracker/add", json={**body, "weight": 71})
    assert response.status_code == 409
    assert response.json["error"] == "conflict"
    assert db.session.scalar(db.select(Progress.weight)) == 70
    assert db.session.scalar(db.select(db.func.count(Progress.id))) == 1


def test_invalid_request_key_is_rejected_before_writing(logged_in):
    response = logged_in.post("/api/tracker/add", json={**entry(), "request_key": "invalid"})
    assert response.status_code == 400
    assert db.session.scalar(db.select(db.func.count(Progress.id))) == 0


def test_request_keys_are_scoped_to_the_owner(logged_in):
    body = entry()
    first = logged_in.post("/api/tracker/add", json=body)
    other = User(email="other-request@example.test", password="!disabled", is_verified=1)
    db.session.add(other)
    db.session.commit()
    with logged_in.session_transaction() as session:
        session["user_id"] = other.id
        session["auth_version"] = other.auth_version
    second = logged_in.post("/api/tracker/add", json=body)
    assert second.status_code == 201
    assert first.json["record"]["id"] != second.json["record"]["id"]


def test_clients_without_request_keys_keep_existing_create_semantics(logged_in):
    body = entry()
    del body["request_key"]
    first = logged_in.post("/api/tracker/add", json=body)
    second = logged_in.post("/api/tracker/add", json=body)
    assert first.json["record"]["id"] != second.json["record"]["id"]


def test_uppercase_uuid_replays_the_same_canonical_request(logged_in):
    body = entry()
    first = logged_in.post("/api/tracker/add", json=body)
    second = logged_in.post("/api/tracker/add", json={**body, "request_key": body["request_key"].upper()})
    assert first.json == second.json

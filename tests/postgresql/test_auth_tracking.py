from flask_migrate import upgrade

from app.extensions import db
from app.models import Progress, User
from app.services.passwords import hash_password


def test_cross_app_otp_and_owned_progress(postgres_app_factory, monkeypatch):
    app = postgres_app_factory()
    with app.app_context():
        upgrade()
    sent = []
    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: sent.append(code))
    credentials = {"email": "owner@example.test", "password": "postgres owner password"}
    assert app.test_client().post("/api/auth/signup", json=credentials).status_code == 202
    assert len(sent) == 1

    # A separate application must consume the persisted challenge, not worker-local state.
    other_app = postgres_app_factory()
    owner = other_app.test_client()
    verification = {**credentials, "otp": sent[0]}
    assert owner.post("/api/auth/verify-otp", json=verification).status_code == 200
    assert owner.post("/api/auth/verify-otp", json=verification).status_code == 400
    assert owner.post("/api/auth/login", json=credentials).status_code == 200
    assert owner.get("/health/ready").status_code == 200

    entry = {"weight": 70, "calories": 2100, "date": "2024-06-01"}
    created = owner.post("/api/tracker/add", json=entry)
    assert created.status_code == 201
    record_id = created.json["record"]["id"]
    with app.app_context():
        db.session.add(
            User(
                email="other@example.test",
                password=hash_password("postgres other password"),
                is_verified=1,
            )
        )
        db.session.add(Progress(email=credentials["email"], weight=71, calories=2000))
        db.session.commit()
    history = owner.get("/api/tracker/history").json
    assert history["total"] == 2
    assert [record["date"] for record in history["records"]] == ["2024-06-01", None]

    stranger = app.test_client()
    assert (
        stranger.post(
            "/api/auth/login",
            json={"email": "other@example.test", "password": "postgres other password"},
        ).status_code
        == 200
    )
    assert stranger.get("/api/tracker/history").json["total"] == 0
    assert stranger.get("/api/tracker/get/owner@example.test").status_code == 403
    assert stranger.put(f"/api/tracker/{record_id}", json=entry).status_code == 404
    assert stranger.delete(f"/api/tracker/{record_id}").status_code == 404
    updated = owner.put(f"/api/tracker/{record_id}", json={**entry, "weight": 72})
    assert updated.status_code == 200
    assert updated.json["record"]["weight"] == 72
    assert owner.delete(f"/api/tracker/{record_id}").status_code == 200
    assert owner.get("/api/tracker/history").json["total"] == 1
    assert owner.post("/api/auth/logout").status_code == 200
    assert owner.get("/api/tracker/history").status_code == 401

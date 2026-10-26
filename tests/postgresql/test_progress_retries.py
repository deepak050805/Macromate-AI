from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, local
from uuid import uuid4

import pytest
from flask_migrate import upgrade
from sqlalchemy import text

from app.extensions import db
from app.models import Progress, User
from app.services import tracking


@pytest.mark.parametrize("different_payload", [False, True])
def test_concurrent_create_retries_use_the_unique_owner_identity(
    postgres_app_factory, monkeypatch, different_payload
):
    apps = [postgres_app_factory(), postgres_app_factory()]
    with apps[0].app_context():
        upgrade()
        account = User(email="retry-race@example.test", password="!disabled", is_verified=1)
        db.session.add(account)
        db.session.commit()
        identity = (account.id, account.auth_version)

    barrier = Barrier(2)
    worker_state = local()
    original = tracking._request_record

    def synchronized_lookup(email, key):
        record = original(email, key)
        if record is None and not getattr(worker_state, "synchronized", False):
            worker_state.synchronized = True
            barrier.wait(timeout=10)
        return record

    monkeypatch.setattr(tracking, "_request_record", synchronized_lookup)
    key = str(uuid4())

    def save(app, weight):
        with app.app_context():
            db.session.execute(text("SET LOCAL lock_timeout = '10s'"))
            db.session.execute(text("SET LOCAL statement_timeout = '15s'"))
            with app.test_client() as client:
                with client.session_transaction() as session:
                    session["user_id"], session["auth_version"] = identity
                response = client.post("/api/tracker/add", json={
                    "date": "2024-01-01", "weight": weight,
                    "calories": 2000, "request_key": key,
                })
                return response.status_code, response.json

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(save, apps[0], 70),
                   executor.submit(save, apps[1], 71 if different_payload else 70)]
        outcomes = [future.result(timeout=30) for future in futures]
    assert sorted(status for status, body in outcomes) == ([201, 409] if different_payload else [201, 201])
    with apps[0].app_context():
        records = db.session.scalars(db.select(Progress)).all()
        assert len(records) == 1
        assert records[0].request_key == key
        successful = [body["record"] for status, body in outcomes if status == 201]
        assert all(record["id"] == records[0].id for record in successful)
        assert all(record["weight"] == records[0].weight for record in successful)

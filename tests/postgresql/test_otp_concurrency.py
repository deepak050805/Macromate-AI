import queue
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from flask_migrate import upgrade
from sqlalchemy import text

from app.extensions import db
from app.models import Otp, User
from app.services.passwords import hash_password, verify_password

EMAIL = "contended@example.test"
ORIGINAL_PASSWORD = "original fictional password"
FINAL_PASSWORD = "final fictional password"
INITIAL_AUTH_VERSION = 7


def prepare_challenge(factory, monkeypatch, purpose="verify"):
    app = factory()
    with app.app_context():
        upgrade()
        user = User(
            email=EMAIL,
            password=hash_password(ORIGINAL_PASSWORD),
            is_verified=int(purpose == "reset"),
            auth_version=INITIAL_AUTH_VERSION,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    sent = []
    monkeypatch.setattr(
        "app.services.otp.send_code", lambda email, code: sent.append((email, code))
    )
    path = "/api/auth/request-reset" if purpose == "reset" else "/api/auth/send-otp"
    assert app.test_client().post(path, json={"email": EMAIL}).status_code == 202
    assert len(sent) == 1
    return app, user_id, sent


def contended_requests(observer_app, actor_apps, user_id, path, payload):
    """Observe both requests blocked behind a real account-row transaction."""
    with observer_app.app_context():
        engine = db.engine
    backends = queue.Queue()

    def request(app):
        with app.app_context():
            db.session.execute(text("SET LOCAL lock_timeout = '20s'"))
            db.session.execute(text("SET LOCAL statement_timeout = '20s'"))
            backends.put(db.session.scalar(text("SELECT pg_backend_pid()")))
            response = app.test_client().post(path, json=payload)
            return response.status_code, response.json

    with ThreadPoolExecutor(max_workers=len(actor_apps)) as executor:
        with engine.begin() as holder:
            holder.execute(
                text("SELECT id FROM users WHERE id = :id FOR UPDATE"), {"id": user_id}
            ).one()
            holder_pid = holder.scalar(text("SELECT pg_backend_pid()"))
            futures = [executor.submit(request, app) for app in actor_apps]
            pids = [backends.get(timeout=10) for _ in actor_apps]
            assert len(set(pids + [holder_pid])) == len(pids) + 1
            deadline = time.monotonic() + 5
            blocked = False
            with engine.connect() as observer:
                while time.monotonic() < deadline:
                    blockers = {
                        pid: set(
                            observer.scalar(text("SELECT pg_blocking_pids(:pid)"), {"pid": pid})
                        )
                        for pid in pids
                    }
                    # A waiter can queue behind another waiter rather than directly
                    # behind the holder. Follow that actual blocking relationship.
                    reachable = {holder_pid}
                    for _ in pids:
                        reachable.update(
                            pid for pid, parents in blockers.items() if parents & reachable
                        )
                    if all(pid in reachable for pid in pids):
                        blocked = True
                        break
                    time.sleep(0.02)
            assert blocked, "Both requests must contend behind the held account row"
        # Release the observer's row lock before joining the actual API requests.
        return [future.result(timeout=30) for future in futures]


@pytest.mark.parametrize("purpose", ["verify", "reset"])
def test_competing_requests_consume_code_once(postgres_app_factory, monkeypatch, purpose):
    app, user_id, sent = prepare_challenge(postgres_app_factory, monkeypatch, purpose)
    actors = [postgres_app_factory(), postgres_app_factory()]
    path = "/api/auth/reset-password" if purpose == "reset" else "/api/auth/verify-otp"
    responses = contended_requests(
        app,
        actors,
        user_id,
        path,
        {"email": EMAIL, "otp": sent[0][1], "password": FINAL_PASSWORD},
    )
    assert sorted(status for status, _ in responses) == [200, 400]
    assert next(body for status, body in responses if status == 400)["error"] == "validation_error"
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.is_verified == 1
        assert user.auth_version == INITIAL_AUTH_VERSION + 1
        assert verify_password(user.password, FINAL_PASSWORD)
        assert not verify_password(user.password, ORIGINAL_PASSWORD)
        assert db.session.get(Otp, user_id) is None


@pytest.mark.parametrize("near_limit", [False, True], ids=["budget-available", "one-attempt-left"])
def test_concurrent_invalid_codes_preserve_attempt_budget(
    postgres_app_factory, monkeypatch, near_limit
):
    app, user_id, sent = prepare_challenge(postgres_app_factory, monkeypatch)
    limit = app.config["OTP_MAX_ATTEMPTS"]
    initial_attempts = limit - 1 if near_limit else 0
    with app.app_context():
        challenge = db.session.get(Otp, user_id)
        challenge.attempts = initial_attempts
        db.session.commit()
    actors = [postgres_app_factory(), postgres_app_factory()]
    wrong_code = "999999" if sent[0][1] == "000000" else "000000"
    responses = contended_requests(
        app,
        actors,
        user_id,
        "/api/auth/verify-otp",
        {"email": EMAIL, "otp": wrong_code, "password": FINAL_PASSWORD},
    )
    assert [status for status, _ in responses] == [400, 400]
    assert all(body["error"] == "validation_error" for _, body in responses)
    expected_attempts = min(initial_attempts + len(actors), limit)
    with app.app_context():
        assert db.session.get(Otp, user_id).attempts == expected_attempts
        assert db.session.get(User, user_id).auth_version == INITIAL_AUTH_VERSION

    valid = app.test_client().post(
        "/api/auth/verify-otp",
        json={"email": EMAIL, "otp": sent[0][1], "password": FINAL_PASSWORD},
    )
    assert valid.status_code == (400 if expected_attempts == limit else 200)
    with app.app_context():
        user = db.session.get(User, user_id)
        if expected_attempts == limit:
            assert db.session.get(Otp, user_id).attempts == limit
            assert user.is_verified == 0
            assert user.auth_version == INITIAL_AUTH_VERSION
            assert verify_password(user.password, ORIGINAL_PASSWORD)
        else:
            assert db.session.get(Otp, user_id) is None
            assert user.is_verified == 1
            assert user.auth_version == INITIAL_AUTH_VERSION + 1

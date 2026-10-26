from concurrent.futures import ThreadPoolExecutor
from threading import Event

from flask_migrate import upgrade
from sqlalchemy import text

from app.extensions import db
from app.models import User
from app.services import auth
from app.services.passwords import hash_password, verify_password


def test_password_change_refreshes_an_identity_revoked_before_locking(postgres_app_factory, monkeypatch):
    first, second = postgres_app_factory(), postgres_app_factory()
    with first.app_context():
        upgrade()
        user = User(email="password-race@example.test", password=hash_password("original fixture password"), is_verified=1)
        db.session.add(user)
        db.session.commit()
        identity = user.id, user.auth_version
    reached_lock, release = Event(), Event()
    original = auth.by_id

    def held_lookup(user_id, lock=False):
        if lock:
            reached_lock.set()
            if not release.wait(timeout=10):
                raise RuntimeError("Password-change lock gate timed out")
        return original(user_id, lock=lock)

    monkeypatch.setattr(auth, "by_id", held_lookup)

    def change():
        with first.app_context():
            db.session.execute(text("SET LOCAL lock_timeout = '10s'"))
            db.session.execute(text("SET LOCAL statement_timeout = '15s'"))
            with first.test_client() as client:
                with client.session_transaction() as session:
                    session["user_id"], session["auth_version"] = identity
                return client.post("/api/auth/change-password", json={
                    "current_password": "original fixture password",
                    "password": "stale requested replacement",
                }).status_code

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(change)
        try:
            assert reached_lock.wait(timeout=10)
            with second.app_context():
                user = db.session.get(User, identity[0])
                user.password = hash_password("externally reset fixture password")
                user.auth_version += 1
                db.session.commit()
        finally:
            release.set()
        assert future.result(timeout=30) == 401
    with second.app_context():
        user = db.session.get(User, identity[0])
        assert user.auth_version == identity[1] + 1
        assert verify_password(user.password, "externally reset fixture password")

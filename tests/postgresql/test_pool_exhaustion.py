import time

import pytest

from app import create_app
from app.extensions import db


@pytest.mark.parametrize("path", ["/health/ready", "/api/tracker/history", "/dashboard"])
def test_exhausted_postgres_pool_returns_safe_errors_and_recovers(postgres_app_factory, path):
    # The fixture has already validated loopback identity and created an owned schema.
    base = postgres_app_factory()
    settings = dict(base.config)
    settings["SQLALCHEMY_ENGINE_OPTIONS"] = {
        **settings["SQLALCHEMY_ENGINE_OPTIONS"], "pool_size": 1, "max_overflow": 0, "pool_timeout": 0.2,
    }
    app = create_app(settings)
    with app.app_context():
        db.create_all()
        client = app.test_client()
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["auth_version"] = 1
        connection = db.engine.connect()
        try:
            started = time.monotonic()
            response = client.get(path)
            assert response.status_code == 503
            assert time.monotonic() - started < 2
            assert "QueuePool" not in response.text
            assert client.get("/health/live").status_code == 200
        finally:
            connection.close()
        try:
            assert client.get("/health/ready").status_code == 200
        finally:
            db.session.remove()
            db.engine.dispose()

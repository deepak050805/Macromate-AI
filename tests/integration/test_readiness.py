import pytest
from flask_migrate import upgrade
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.extensions import db
from app.models import Otp, Progress, User


def empty_app():
    return create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "RATELIMIT_ENABLED": False}
    )


def test_empty_database_is_not_ready_and_remains_unmodified():
    app = empty_app()
    client = app.test_client()
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json == {"status": "unavailable"}
    assert client.get("/health/live").status_code == 200
    with app.app_context():
        assert inspect(db.engine).get_table_names() == []


def test_legacy_schema_is_not_ready():
    app = empty_app()
    with app.app_context():
        upgrade(revision="0001")
    response = app.test_client().get("/health/ready")
    assert response.status_code == 503
    assert response.json == {"status": "unavailable"}


@pytest.mark.parametrize("model", [User, Progress, Otp])
def test_missing_required_table_is_not_ready(app, client, model):
    model.__table__.drop(db.engine)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json == {"status": "unavailable"}


def test_connection_failure_stays_generic_and_liveness_independent(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise SQLAlchemyError("private-driver-diagnostic")

    with monkeypatch.context() as outage:
        outage.setattr(db.session, "execute", unavailable)
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json == {"status": "unavailable"}
        assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200

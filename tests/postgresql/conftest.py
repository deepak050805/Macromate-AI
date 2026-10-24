"""Run only against an explicitly configured loopback test database."""

import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema

from app import create_app
from app.extensions import db


@pytest.fixture
def postgres_app_factory():
    value = os.getenv("TEST_POSTGRES_URL")
    if not value:
        pytest.fail("Set TEST_POSTGRES_URL to a disposable local macromate_test database")
    url = make_url(value)
    if (
        url.drivername not in {"postgresql", "postgresql+psycopg2"}
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or url.database != "macromate_test"
        or url.username != "macromate_test"
    ):
        pytest.fail("PostgreSQL tests require a loopback macromate_test database and user")
    url = url.set(drivername="postgresql+psycopg2")
    schema = "macromate_test_" + uuid.uuid4().hex
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    apps = []

    def factory():
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "postgresql-test-only-key-not-for-deployment",
                "SQLALCHEMY_DATABASE_URI": url.render_as_string(hide_password=False),
                "SQLALCHEMY_ENGINE_OPTIONS": {
                    "connect_args": {"options": f"-csearch_path={schema}", "connect_timeout": 5}
                },
                "WTF_CSRF_ENABLED": False,
                "RATELIMIT_ENABLED": False,
            }
        )
        apps.append(app)
        return app

    try:
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        try:
            yield factory
        finally:
            for app in apps:
                with app.app_context():
                    db.session.remove()
                    db.engine.dispose()
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()

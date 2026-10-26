"""Run only against an explicitly configured loopback test database."""

import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.schema import CreateSchema, DropSchema

from app import create_app
from app.extensions import db


def postgres_test_target(value):
    """Validate the effective connection target, including libpq query overrides."""
    message = "PostgreSQL tests require a loopback macromate_test database and user"
    try:
        url = make_url(value)
        port = url.port if url.port is not None else 5432
    except (ArgumentError, TypeError, ValueError):
        raise ValueError(message) from None
    if (
        url.drivername not in {"postgresql", "postgresql+psycopg2"}
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or url.database != "macromate_test"
        or url.username != "macromate_test"
        or not 1 <= port <= 65535
    ):
        raise ValueError(message)
    routing_options = {
        "host", "hostaddr", "port", "dbname", "database", "user", "username",
        "password", "service", "servicefile", "passfile", "options", "dsn",
    }
    if any(key.lower() in routing_options for key in url.query):
        raise ValueError("PostgreSQL test URLs must not override connection targets or identities")
    address = "127.0.0.1" if url.host == "localhost" else url.host
    # Explicit libpq parameters override PGHOSTADDR/PGSERVICE/PGPORT defaults.
    # Keep the schema-control connection independent from ambient PGOPTIONS too.
    connect_args = {
        "host": url.host, "hostaddr": address, "port": port,
        "user": "macromate_test", "dbname": "macromate_test",
        "connect_timeout": 5, "options": "-csearch_path=pg_catalog",
    }
    return url.set(drivername="postgresql+psycopg2"), connect_args


@pytest.fixture
def postgres_app_factory():
    value = os.getenv("TEST_POSTGRES_URL")
    if not value:
        pytest.fail("Set TEST_POSTGRES_URL to a disposable local macromate_test database")
    try:
        url, connect_args = postgres_test_target(value)
    except ValueError as error:
        pytest.fail(str(error))
    schema = "macromate_test_" + uuid.uuid4().hex
    engine = create_engine(url, connect_args=connect_args)
    apps = []

    def factory():
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "postgresql-test-only-key-not-for-deployment",
                "SQLALCHEMY_DATABASE_URI": url.render_as_string(hide_password=False),
                "SQLALCHEMY_ENGINE_OPTIONS": {
                    "connect_args": {**connect_args, "options": f"-csearch_path={schema}"}
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

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2


PATH = Path(__file__).resolve().parents[1] / "postgresql" / "conftest.py"
SPEC = importlib.util.spec_from_file_location("postgres_fixture_safety", PATH)
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)


@pytest.mark.parametrize("key", [
    "host", "hostaddr", "port", "dbname", "database", "user", "username",
    "password", "service", "servicefile", "passfile", "options", "dsn", "HOSTADDR",
])
def test_postgres_fixture_rejects_query_routing_and_identity_overrides(key):
    value = f"postgresql://macromate_test:disposable@127.0.0.1/macromate_test?{key}=private-value"
    with pytest.raises(ValueError, match="must not override") as error:
        FIXTURE.postgres_test_target(value)
    assert "private-value" not in str(error.value)


@pytest.mark.parametrize("host,address", [
    ("127.0.0.1", "127.0.0.1"), ("localhost", "127.0.0.1"), ("[::1]", "::1"),
])
def test_postgres_fixture_pins_all_effective_identity_and_routing_parameters(host, address, monkeypatch):
    monkeypatch.setenv("PGHOSTADDR", "192.0.2.1")
    monkeypatch.setenv("PGSERVICE", "nonexistent-ambient-service")
    monkeypatch.setenv("PGPORT", "6543")
    monkeypatch.setenv("PGOPTIONS", "-csearch_path=unrelated")
    url, connect_args = FIXTURE.postgres_test_target(
        f"postgresql://macromate_test:disposable@{host}:5544/macromate_test"
    )
    # Inspect the exact driver kwargs without opening any socket.
    positional, dialect_args = PGDialect_psycopg2().create_connect_args(url)
    assert positional == []
    effective = {**dialect_args, **connect_args}
    assert effective["hostaddr"] == address
    assert effective["port"] == 5544
    assert effective["dbname"] == effective["user"] == "macromate_test"
    assert effective["options"] == "-csearch_path=pg_catalog"
    assert effective["connect_timeout"] == 5


def test_postgres_fixture_uses_a_fixed_default_port_instead_of_pgport(monkeypatch):
    monkeypatch.setenv("PGPORT", "6543")
    _, connect_args = FIXTURE.postgres_test_target(
        "postgresql://macromate_test:disposable@127.0.0.1/macromate_test"
    )
    assert connect_args["port"] == 5432


def test_postgres_fixture_retains_nonrouting_connection_options():
    url, connect_args = FIXTURE.postgres_test_target(
        "postgresql://macromate_test:disposable@127.0.0.1/macromate_test?sslmode=disable"
    )
    assert url.query["sslmode"] == "disable"
    assert connect_args["hostaddr"] == "127.0.0.1"


def test_schema_control_and_every_app_engine_receive_pinned_targets(monkeypatch):
    monkeypatch.setenv("TEST_POSTGRES_URL", "postgresql://macromate_test:disposable@127.0.0.1:5544/macromate_test")
    control_engine = MagicMock()
    create_engine = MagicMock(return_value=control_engine)
    create_app = MagicMock(side_effect=lambda config: MagicMock())
    monkeypatch.setattr(FIXTURE, "create_engine", create_engine)
    monkeypatch.setattr(FIXTURE, "create_app", create_app)
    monkeypatch.setattr(FIXTURE, "db", MagicMock())
    lifecycle = FIXTURE.postgres_app_factory.__wrapped__()
    factory = next(lifecycle)
    try:
        factory()
        factory()
        arguments = [create_engine.call_args.kwargs["connect_args"], *(
            call.args[0]["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"]
            for call in create_app.call_args_list
        )]
        assert len(arguments) == 3
        for target in arguments:
            assert target["host"] == target["hostaddr"] == "127.0.0.1"
            assert target["port"] == 5544
            assert target["user"] == target["dbname"] == "macromate_test"
        assert arguments[0]["options"] == "-csearch_path=pg_catalog"
        assert all(target["options"].startswith("-csearch_path=macromate_test_") for target in arguments[1:])
    finally:
        lifecycle.close()


@pytest.mark.parametrize("value", [
    "postgresql://macromate_test:private@remote.invalid/macromate_test",
    "postgresql://another_user:private@127.0.0.1/macromate_test",
    "postgresql://macromate_test:private@127.0.0.1/another_database",
    "postgresql://macromate_test:private@127.0.0.1:65536/macromate_test",
    "postgresql://macromate_test:private@127.0.0.1:0/macromate_test",
    "not-a-connection-url-private",
])
def test_postgres_fixture_rejects_non_test_targets_without_echoing_credentials(value):
    with pytest.raises(ValueError) as error:
        FIXTURE.postgres_test_target(value)
    assert "private" not in str(error.value)

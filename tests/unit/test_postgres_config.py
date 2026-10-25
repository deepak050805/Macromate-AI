import pytest

from app.config import configuration


@pytest.fixture(autouse=True)
def isolated_connection_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.delenv("PGCONNECT_TIMEOUT", raising=False)


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://", "postgresql+psycopg2://"])
def test_postgres_defaults_to_five_second_connection_timeout(scheme):
    values = configuration({"SQLALCHEMY_DATABASE_URI": scheme + "localhost/test"})
    options = values["SQLALCHEMY_ENGINE_OPTIONS"]
    assert options["pool_pre_ping"] is True
    assert options["connect_args"]["connect_timeout"] == 5


@pytest.mark.parametrize("timeout", [0, 9])
def test_factory_timeout_preserves_uri_precedence_and_caller_options(timeout):
    custom = {
        "pool_pre_ping": False,
        "connect_args": {"connect_timeout": timeout, "application_name": "test-only"},
    }
    values = configuration(
        {
            "SQLALCHEMY_DATABASE_URI": "postgresql://localhost/test?connect_timeout=7",
            "SQLALCHEMY_ENGINE_OPTIONS": custom,
        }
    )
    options = values["SQLALCHEMY_ENGINE_OPTIONS"]
    assert options["pool_pre_ping"] is False
    assert options["connect_args"] == {
        "connect_timeout": timeout,
        "application_name": "test-only",
    }
    assert custom == {
        "pool_pre_ping": False,
        "connect_args": {"connect_timeout": timeout, "application_name": "test-only"},
    }


def test_other_engine_options_keep_connection_default_without_mutating_caller():
    custom = {"pool_size": 4, "connect_args": {"application_name": "test-only"}}
    values = configuration(
        {
            "SQLALCHEMY_DATABASE_URI": "postgresql://localhost/test",
            "SQLALCHEMY_ENGINE_OPTIONS": custom,
        }
    )
    assert values["SQLALCHEMY_ENGINE_OPTIONS"]["pool_size"] == 4
    assert values["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"] == {
        "connect_timeout": 5,
        "application_name": "test-only",
    }
    assert custom == {"pool_size": 4, "connect_args": {"application_name": "test-only"}}


@pytest.mark.parametrize("timeout", ["0", "7"])
def test_uri_timeout_is_not_shadowed_by_factory_default(timeout):
    uri = f"postgresql://localhost/test?connect_timeout={timeout}"
    values = configuration({"SQLALCHEMY_DATABASE_URI": uri})
    assert values["SQLALCHEMY_DATABASE_URI"].endswith(f"?connect_timeout={timeout}")
    assert "connect_timeout" not in values["SQLALCHEMY_ENGINE_OPTIONS"].get("connect_args", {})


@pytest.mark.parametrize("timeout", ["0", "7"])
def test_libpq_environment_timeout_is_not_shadowed(monkeypatch, timeout):
    monkeypatch.setenv("PGCONNECT_TIMEOUT", timeout)
    values = configuration({"SQLALCHEMY_DATABASE_URI": "postgresql://localhost/test"})
    assert "connect_timeout" not in values["SQLALCHEMY_ENGINE_OPTIONS"].get("connect_args", {})


def test_sqlite_does_not_receive_postgres_connection_options():
    custom = {"connect_args": {"check_same_thread": False}}
    values = configuration(
        {"SQLALCHEMY_DATABASE_URI": "sqlite://", "SQLALCHEMY_ENGINE_OPTIONS": custom}
    )
    assert values["SQLALCHEMY_ENGINE_OPTIONS"] == custom
    assert "connect_timeout" not in custom["connect_args"]

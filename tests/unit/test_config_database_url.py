"""Connection URL errors must be actionable without disclosing operator secrets."""

import pytest

from app.config import configuration


@pytest.fixture(autouse=True)
def isolated_database_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "memory://")


@pytest.mark.parametrize("value", [None, True, 42, {}, [], b"sqlite://", "", " \t"])
def test_database_url_requires_nonblank_text(value):
    with pytest.raises(ValueError, match="DATABASE_URL"):
        configuration({"SQLALCHEMY_DATABASE_URI": value})


@pytest.mark.parametrize(
    "value",
    [
        "private-credential-without-a-url-scheme",
        "postgresql://fixture:private-password@localhost:private-port/database",
        "postgresql://fixture:private-password@localhost:12.5/database",
    ],
)
def test_malformed_url_errors_do_not_echo_credentials_or_parser_diagnostics(value):
    with pytest.raises(ValueError, match="DATABASE_URL") as caught:
        configuration({"SQLALCHEMY_DATABASE_URI": value})
    assert "private-" not in str(caught.value)
    assert caught.value.__suppress_context__ is True


def test_factory_url_overrides_malformed_environment_before_parsing(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fixture:private-password@localhost:bad/db")
    values = configuration({"SQLALCHEMY_DATABASE_URI": "sqlite://"})
    assert values["SQLALCHEMY_DATABASE_URI"] == "sqlite://"


def test_valid_database_query_and_password_are_preserved_without_connecting():
    uri = "postgresql://fixture:fictional%40password@localhost/database?sslmode=require"
    values = configuration({"SQLALCHEMY_DATABASE_URI": uri})
    assert values["SQLALCHEMY_DATABASE_URI"] == uri.replace(
        "postgresql://", "postgresql+psycopg2://", 1
    )
    assert values["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"]["connect_timeout"] == 5

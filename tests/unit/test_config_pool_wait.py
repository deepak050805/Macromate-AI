import pytest

from app.config import configuration


def test_postgres_pool_wait_is_bounded_without_mutating_factory_options(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_POOL_TIMEOUT_SECONDS", "5")
    settings = {"SQLALCHEMY_DATABASE_URI": "postgresql://localhost/unused", "SQLALCHEMY_ENGINE_OPTIONS": {"pool_size": 2}}
    values = configuration(settings)
    assert values["SQLALCHEMY_ENGINE_OPTIONS"]["pool_timeout"] == 5
    assert settings["SQLALCHEMY_ENGINE_OPTIONS"] == {"pool_size": 2}


def test_explicit_pool_timeout_preserves_fractional_operator_override():
    values = configuration({"APP_ENV": "testing", "SQLALCHEMY_DATABASE_URI": "postgresql://localhost/unused", "SQLALCHEMY_ENGINE_OPTIONS": {"pool_timeout": 0.2}})
    assert values["SQLALCHEMY_ENGINE_OPTIONS"]["pool_timeout"] == 0.2


def test_sqlite_receives_no_pool_wait_option():
    values = configuration({"APP_ENV": "testing", "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    assert "pool_timeout" not in values["SQLALCHEMY_ENGINE_OPTIONS"]


@pytest.mark.parametrize("value", [0, 301, True, None, "invalid", "1.5"])
def test_invalid_pool_wait_fails_with_named_setting(value):
    with pytest.raises(ValueError, match="DATABASE_POOL_TIMEOUT_SECONDS"):
        configuration({"APP_ENV": "testing", "SQLALCHEMY_DATABASE_URI": "sqlite://", "DATABASE_POOL_TIMEOUT_SECONDS": value})

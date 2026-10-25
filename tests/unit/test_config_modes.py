"""Application mode must select defaults and startup checks from the same source."""

import pytest

from app.config import configuration


@pytest.fixture(autouse=True)
def isolated_mode_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    for key in (
        "SECRET_KEY",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_DEFAULT_SENDER",
        "TRUSTED_HOSTS",
        "RATELIMIT_STORAGE_URI",
    ):
        monkeypatch.delenv(key, raising=False)


def production_settings():
    return {
        "APP_ENV": "production",
        "SECRET_KEY": "fictional-production-key-" * 3,
        "MAIL_USERNAME": "fixture",
        "MAIL_PASSWORD": "fictional-password",
        "MAIL_DEFAULT_SENDER": "fixture@example.test",
        "TRUSTED_HOSTS": ["example.test"],
        "SQLALCHEMY_DATABASE_URI": "postgresql://localhost/unused",
        "RATELIMIT_STORAGE_URI": "redis://localhost:6379",
    }


def test_factory_production_mode_rejects_development_only_defaults():
    with pytest.raises(ValueError, match="Production requires"):
        configuration({"APP_ENV": "production"})


def test_factory_production_mode_defaults_to_secure_cookies_without_mutating_settings():
    settings = production_settings()
    values = configuration(settings)
    assert values["APP_ENV"] == "production"
    assert values["SESSION_COOKIE_SECURE"] is True
    assert "SESSION_COOKIE_SECURE" not in settings
    assert settings["SQLALCHEMY_DATABASE_URI"].startswith("postgresql://")


def test_explicit_insecure_cookie_cannot_disable_factory_production_safeguards():
    with pytest.raises(ValueError, match="secure cookies"):
        configuration({**production_settings(), "SESSION_COOKIE_SECURE": False})


def test_factory_testing_mode_overrides_production_environment_defaults(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    values = configuration({"APP_ENV": "testing"})
    assert values["APP_ENV"] == "testing"
    assert values["SESSION_COOKIE_SECURE"] is False
    assert len(values["SECRET_KEY"]) >= 32


@pytest.mark.parametrize("mode", ["prod", "PRODUCTION", "", None, 42, []])
def test_unknown_factory_modes_fail_with_a_named_error(mode):
    with pytest.raises(ValueError, match="APP_ENV"):
        configuration({"APP_ENV": mode})


@pytest.mark.parametrize("mode", ["prod", "PRODUCTION", ""])
def test_unknown_environment_modes_fail_with_a_named_error(monkeypatch, mode):
    monkeypatch.setenv("APP_ENV", mode)
    with pytest.raises(ValueError, match="APP_ENV"):
        configuration()


@pytest.mark.parametrize("mode", ["development", "testing"])
def test_supported_nonproduction_modes_keep_local_defaults(mode):
    values = configuration({"APP_ENV": mode})
    assert values["APP_ENV"] == mode
    assert values["SESSION_COOKIE_SECURE"] is False


def test_absent_mode_defaults_to_development(monkeypatch):
    monkeypatch.delenv("APP_ENV")
    assert configuration()["APP_ENV"] == "development"

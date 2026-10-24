import pytest

from app.config import configuration


def test_missing_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        configuration()


def test_production_secrets(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="Production requires"):
        configuration()


def test_unsafe_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    base = {
        "SECRET_KEY": "x" * 64,
        "MAIL_USERNAME": "example",
        "MAIL_PASSWORD": "placeholder",
        "MAIL_DEFAULT_SENDER": "example@example.test",
        "TRUSTED_HOSTS": ["localhost"],
        "SQLALCHEMY_DATABASE_URI": "postgresql://localhost/test",
        "RATELIMIT_STORAGE_URI": "redis://localhost:6379",
    }
    assert configuration(base)["SESSION_COOKIE_SECURE"]
    for key, value in [
        ("SECRET_KEY", "short"),
        ("SESSION_COOKIE_SECURE", False),
        ("SQLALCHEMY_DATABASE_URI", "sqlite://"),
        ("RATELIMIT_STORAGE_URI", "memory://"),
        ("MAIL_USE_TLS", False),
    ]:
        with pytest.raises(ValueError):
            configuration({**base, key: value})


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://", "postgresql+psycopg2://"])
def test_postgres_url_uses_installed_driver(scheme):
    values = configuration({"SQLALCHEMY_DATABASE_URI": scheme + "localhost/driver_test"})
    assert values["SQLALCHEMY_DATABASE_URI"] == "postgresql+psycopg2://localhost/driver_test"

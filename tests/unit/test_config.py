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


@pytest.mark.parametrize("scheme", ["redis", "rediss"])
def test_redis_storage_has_finite_timeouts_and_no_request_retries(scheme):
    values = configuration(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "RATELIMIT_STORAGE_URI": f"{scheme}://localhost/15",
        }
    )
    options = values["RATELIMIT_STORAGE_OPTIONS"]
    assert options["socket_connect_timeout"] == 2
    assert options["socket_timeout"] == 2
    assert options["retry"].get_retries() == 0


def test_custom_redis_options_preserve_other_timeout_defaults():
    custom = {"socket_timeout": 0.25}
    values = configuration(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "RATELIMIT_STORAGE_URI": "redis://localhost/15",
            "RATELIMIT_STORAGE_OPTIONS": custom,
        }
    )
    assert values["RATELIMIT_STORAGE_OPTIONS"]["socket_timeout"] == 0.25
    assert values["RATELIMIT_STORAGE_OPTIONS"]["socket_connect_timeout"] == 2
    assert custom == {"socket_timeout": 0.25}


def test_memory_storage_does_not_receive_redis_options():
    values = configuration(
        {"SQLALCHEMY_DATABASE_URI": "sqlite://", "RATELIMIT_STORAGE_URI": "memory://"}
    )
    assert "RATELIMIT_STORAGE_OPTIONS" not in values

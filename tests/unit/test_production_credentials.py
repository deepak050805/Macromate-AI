import pytest

from app.config import configuration


def production_settings():
    return {
        "APP_ENV": "production", "SECRET_KEY": "fixture-only-secret-" * 3,
        "SQLALCHEMY_DATABASE_URI": "postgresql://localhost/unused",
        "MAIL_USERNAME": "fixture", "MAIL_PASSWORD": "fictional-password",
        "MAIL_DEFAULT_SENDER": "MacroMate <fixture@example.test>",
        "TRUSTED_HOSTS": ["localhost"], "RATELIMIT_STORAGE_URI": "redis://localhost:6379",
    }


@pytest.mark.parametrize("key", ["SECRET_KEY", "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER"])
@pytest.mark.parametrize("value", [" " * 64, ["invalid"] * 32, b"binary" * 10])
def test_production_credentials_require_usable_strings(key, value):
    with pytest.raises(ValueError, match="Production requires"):
        configuration({**production_settings(), key: value})


def test_valid_mail_display_names_and_secret_spaces_are_not_rewritten():
    settings = production_settings()
    settings["SECRET_KEY"] = " " + settings["SECRET_KEY"] + " "
    values = configuration(settings)
    assert values["SECRET_KEY"] == settings["SECRET_KEY"]
    assert values["MAIL_DEFAULT_SENDER"] == settings["MAIL_DEFAULT_SENDER"]

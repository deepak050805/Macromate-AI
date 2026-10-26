"""Invalid SMTP host/header values must fail before any registration request."""

import pytest

from app.config import configuration


@pytest.fixture(autouse=True)
def isolated_smtp_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "memory://")
    monkeypatch.setenv("MAIL_SERVER", "smtp.example.test")
    monkeypatch.setenv("MAIL_DEFAULT_SENDER", "")
    monkeypatch.setenv("MAIL_USERNAME", "")
    monkeypatch.setenv("MAIL_PASSWORD", "")


def production_settings():
    return {
        "APP_ENV": "production",
        "SECRET_KEY": "fictional-production-key-" * 3,
        "SQLALCHEMY_DATABASE_URI": "postgresql://localhost/unused",
        "RATELIMIT_STORAGE_URI": "redis://localhost/15",
        "TRUSTED_HOSTS": ["example.test"],
        "MAIL_USERNAME": "fixture",
        "MAIL_PASSWORD": "fictional-mail-password",
        "MAIL_DEFAULT_SENDER": "MacroMate <sender@example.test>",
    }


@pytest.mark.parametrize(
    "value",
    [None, 12, [], "", " \t", "smtp .example.test", "smtp.example.test\n", "smtp.\x00example.test", "smtp.\ud800.test"],
)
def test_production_requires_a_usable_smtp_hostname(value):
    with pytest.raises(ValueError, match="MAIL_SERVER"):
        configuration({**production_settings(), "MAIL_SERVER": value})


@pytest.mark.parametrize("value", ["sender@example.test\nBcc: private@example.test", "sender\r@example.test", "sender\x00@example.test", "sender\ud800@example.test"])
def test_sender_control_characters_and_unencodable_text_have_safe_diagnostics(value):
    with pytest.raises(ValueError, match="MAIL_DEFAULT_SENDER") as caught:
        configuration({**production_settings(), "MAIL_DEFAULT_SENDER": value})
    assert "private@example.test" not in str(caught.value)
    assert "sender@example.test" not in str(caught.value)


@pytest.mark.parametrize("value", [None, [], 42, " \t"])
def test_configured_development_senders_must_also_be_usable(value):
    with pytest.raises(ValueError, match="MAIL_DEFAULT_SENDER"):
        configuration({"MAIL_DEFAULT_SENDER": value})


def test_blank_development_mail_settings_remain_optional():
    values = configuration({"MAIL_SERVER": "", "MAIL_DEFAULT_SENDER": "", "MAIL_USERNAME": ""})
    assert values["MAIL_SERVER"] == ""
    assert values["MAIL_DEFAULT_SENDER"] == ""


def test_display_names_and_internationalized_smtp_hostnames_are_preserved():
    settings = {
        **production_settings(),
        "MAIL_SERVER": "smtp.b\u00fccher.example",
        "MAIL_DEFAULT_SENDER": "MacroMate Fran\u00e7ais <sender@example.test>",
    }
    values = configuration(settings)
    assert values["MAIL_SERVER"] == settings["MAIL_SERVER"]
    assert values["MAIL_DEFAULT_SENDER"] == settings["MAIL_DEFAULT_SENDER"]


def test_username_fallback_cannot_inject_a_sender_header():
    with pytest.raises(ValueError, match="MAIL_USERNAME"):
        configuration({"MAIL_USERNAME": "fixture\nBcc: private@example.test"})


def test_factory_smtp_host_overrides_an_invalid_environment(monkeypatch):
    monkeypatch.setenv("MAIL_SERVER", "smtp.example.test\n")
    assert configuration({"MAIL_SERVER": "localhost"})["MAIL_SERVER"] == "localhost"

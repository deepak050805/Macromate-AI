import pytest

from app.config import configuration


@pytest.fixture(autouse=True)
def local_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")


@pytest.mark.parametrize("raw,expected", [("true", True), (" TRUE ", True), ("1", True),
    ("yes", True), ("on", True), ("false", False), ("0", False), ("off", False), ("no", False)])
def test_tls_boolean_forms_are_explicit(monkeypatch, raw, expected):
    monkeypatch.setenv("MAIL_USE_TLS", raw)
    assert configuration()["MAIL_USE_TLS"] is expected


def test_misspelled_tls_cannot_silently_disable_encryption(monkeypatch):
    monkeypatch.setenv("MAIL_USE_TLS", "tru")
    with pytest.raises(ValueError, match="MAIL_USE_TLS"):
        configuration()
    assert configuration({"MAIL_USE_TLS": True})["MAIL_USE_TLS"] is True


def test_cookie_boolean_strings_have_their_intended_value():
    assert configuration({"SESSION_COOKIE_SECURE": "false"})["SESSION_COOKIE_SECURE"] is False
    with pytest.raises(ValueError, match="SESSION_COOKIE_SECURE"):
        configuration({"SESSION_COOKIE_SECURE": "invalid"})

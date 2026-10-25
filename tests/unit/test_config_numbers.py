"""Invalid operator settings must fail at startup, before mail/OTP requests."""

import pytest

from app.config import configuration

ENV_NUMBERS = ("MAIL_PORT", "OTP_EXPIRY_SECONDS", "OTP_COOLDOWN_SECONDS")
FACTORY_NUMBERS = (*ENV_NUMBERS, "OTP_MAX_ATTEMPTS")


@pytest.fixture(autouse=True)
def isolated_numeric_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    for key in ENV_NUMBERS:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize(
    "key,value",
    [
        ("MAIL_PORT", "0"),
        ("MAIL_PORT", "65536"),
        ("OTP_EXPIRY_SECONDS", "0"),
        ("OTP_COOLDOWN_SECONDS", "-1"),
    ],
)
def test_environment_bounds_are_validated(monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match=key):
        configuration()


@pytest.mark.parametrize("key", ENV_NUMBERS)
def test_malformed_environment_errors_name_the_setting_without_echoing_its_value(monkeypatch, key):
    diagnostic = "private-invalid-setting-value"
    monkeypatch.setenv(key, diagnostic)
    with pytest.raises(ValueError, match=key) as caught:
        configuration()
    assert diagnostic not in str(caught.value)


@pytest.mark.parametrize(
    "key,value",
    [
        ("MAIL_PORT", 0),
        ("MAIL_PORT", 65536),
        ("OTP_EXPIRY_SECONDS", 0),
        ("OTP_COOLDOWN_SECONDS", -1),
        ("OTP_MAX_ATTEMPTS", 0),
    ],
)
def test_factory_bounds_are_validated(key, value):
    with pytest.raises(ValueError, match=key):
        configuration({key: value})


@pytest.mark.parametrize("key", FACTORY_NUMBERS)
@pytest.mark.parametrize("value", [True, None, 1.5, "not-an-integer"])
def test_factory_booleans_and_nonintegers_are_not_used_as_numeric_settings(key, value):
    with pytest.raises(ValueError, match=key):
        configuration({key: value})


@pytest.mark.parametrize("key", ENV_NUMBERS)
def test_explicit_factory_number_overrides_a_malformed_environment(monkeypatch, key):
    monkeypatch.setenv(key, "malformed")
    settings = {"MAIL_PORT": 587, "OTP_EXPIRY_SECONDS": 300, "OTP_COOLDOWN_SECONDS": 60}
    assert configuration({key: settings[key]})[key] == settings[key]


@pytest.mark.parametrize("values", [(1, 1, 0, 1), (65535, 600, 60, 8)])
def test_valid_numeric_boundaries_and_zero_cooldown_are_preserved(values):
    settings = dict(zip(FACTORY_NUMBERS, values, strict=True))
    result = configuration(settings)
    assert all(result[key] == value for key, value in settings.items())
    assert settings == dict(zip(FACTORY_NUMBERS, values, strict=True))


def test_factory_decimal_strings_are_normalized_before_service_use():
    result = configuration({key: "12" for key in FACTORY_NUMBERS})
    assert all(result[key] == 12 and type(result[key]) is int for key in FACTORY_NUMBERS)


def test_otp_lifetime_that_cannot_be_used_in_timestamp_arithmetic_fails_at_startup(monkeypatch):
    monkeypatch.setenv("OTP_EXPIRY_SECONDS", "9" * 400)
    with pytest.raises(ValueError, match="OTP_EXPIRY_SECONDS"):
        configuration()

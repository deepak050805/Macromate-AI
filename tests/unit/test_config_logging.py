"""Logging configuration fails before logger initialization with private input errors."""

import logging

import pytest

from app.config import configuration


@pytest.fixture(autouse=True)
def isolated_logging_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "memory://")
    monkeypatch.delenv("LOG_LEVEL", raising=False)


@pytest.mark.parametrize("name", ["DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL", "NOTSET"])
def test_builtin_logging_names_are_preserved(name):
    assert configuration({"LOG_LEVEL": name})["LOG_LEVEL"] == name


@pytest.mark.parametrize("raw,expected", [("warning", "WARNING"), (" INFO ", "INFO"), ("debug", "DEBUG")])
def test_operator_logging_names_are_normalized(raw, expected):
    assert configuration({"LOG_LEVEL": raw})["LOG_LEVEL"] == expected


@pytest.mark.parametrize("level", [0, 15, 20, 50])
def test_explicit_integer_thresholds_remain_supported(level):
    assert configuration({"LOG_LEVEL": level})["LOG_LEVEL"] == level


@pytest.mark.parametrize("value", [True, False, None, [], {}, 1.5, "", "20", "private-invalid-level"])
def test_invalid_logging_settings_raise_a_named_sanitized_error(value):
    with pytest.raises(ValueError, match="LOG_LEVEL") as caught:
        configuration({"LOG_LEVEL": value})
    assert "private-invalid-level" not in str(caught.value)


def test_factory_logging_level_overrides_invalid_environment(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "private-invalid-level")
    assert configuration({"LOG_LEVEL": "ERROR"})["LOG_LEVEL"] == "ERROR"


def test_default_logging_level_remains_info():
    assert configuration()["LOG_LEVEL"] == "INFO"


def test_registered_custom_logging_names_keep_their_original_case(monkeypatch):
    monkeypatch.setattr(logging, "getLevelNamesMapping", lambda: {"AuditEvent": 25})
    assert configuration({"LOG_LEVEL": "AuditEvent"})["LOG_LEVEL"] == "AuditEvent"

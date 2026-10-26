"""Redis startup diagnostics must name settings without echoing private URLs."""

import pytest

from app.config import configuration


@pytest.fixture(autouse=True)
def isolated_redis_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "memory://")


@pytest.mark.parametrize("value", [None, True, 42, {}, [], b"memory://", "", " \t"])
def test_storage_url_requires_nonblank_text(value):
    with pytest.raises(ValueError, match="RATELIMIT_STORAGE_URI"):
        configuration({"RATELIMIT_STORAGE_URI": value})


@pytest.mark.parametrize(
    "uri",
    [
        "redis://fixture:private-password@localhost:private-port/15",
        "rediss://fixture:private-password@localhost:65536/15",
        "redis://fixture:private-password@localhost/15?socket_timeout=private-timeout",
    ],
)
def test_redis_parser_errors_do_not_expose_private_values(uri):
    with pytest.raises(ValueError, match="RATELIMIT_STORAGE_URI") as caught:
        configuration({"RATELIMIT_STORAGE_URI": uri})
    assert "private-" not in str(caught.value)
    assert caught.value.__suppress_context__ is True


@pytest.mark.parametrize("value", [False, [], "private-options", 5])
def test_redis_options_require_a_mapping(value):
    with pytest.raises(ValueError, match="RATELIMIT_STORAGE_OPTIONS"):
        configuration({"RATELIMIT_STORAGE_URI": "redis://localhost/15", "RATELIMIT_STORAGE_OPTIONS": value})


def test_valid_redis_url_is_preserved_without_connecting_or_mutating_options():
    uri = "rediss://fixture:fictional%40password@localhost/15?socket_timeout=0.5"
    options = {"socket_connect_timeout": 1}
    values = configuration({"RATELIMIT_STORAGE_URI": uri, "RATELIMIT_STORAGE_OPTIONS": options})
    assert values["RATELIMIT_STORAGE_URI"] == uri
    assert values["RATELIMIT_STORAGE_OPTIONS"]["socket_connect_timeout"] == 1
    assert options == {"socket_connect_timeout": 1}


def test_factory_storage_overrides_a_malformed_environment(monkeypatch):
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "redis://localhost:private-port/15")
    assert configuration({"RATELIMIT_STORAGE_URI": "memory://"})["RATELIMIT_STORAGE_URI"] == "memory://"

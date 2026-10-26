import pytest

from app.config import configuration


@pytest.fixture(autouse=True)
def local_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")


def test_comma_separated_hosts_trim_spaces_and_ignore_empty_items(monkeypatch):
    monkeypatch.setenv("TRUSTED_HOSTS", " localhost, example.test, , .example.test ")
    assert configuration()["TRUSTED_HOSTS"] == ["localhost", "example.test", ".example.test"]


def test_only_blank_host_entries_are_not_a_configured_allowlist(monkeypatch):
    monkeypatch.setenv("TRUSTED_HOSTS", " , , ")
    assert configuration()["TRUSTED_HOSTS"] is None


def test_factory_host_normalization_does_not_change_the_callers_list():
    hosts = [" localhost ", "", "example.test"]
    assert configuration({"TRUSTED_HOSTS": hosts})["TRUSTED_HOSTS"] == ["localhost", "example.test"]
    assert hosts == [" localhost ", "", "example.test"]


@pytest.mark.parametrize("hosts", ["example.test", [123], {"example.test"}])
def test_invalid_factory_host_types_fail_with_a_named_error(hosts):
    with pytest.raises(ValueError, match="TRUSTED_HOSTS"):
        configuration({"TRUSTED_HOSTS": hosts})

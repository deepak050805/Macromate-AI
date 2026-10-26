import pytest

from app.config import configuration


@pytest.mark.parametrize("hops", [-1, 6, True, None, "one", "1.5", 1.5])
def test_invalid_proxy_counts_fail_without_enabling_trust(monkeypatch, hops):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    with pytest.raises(ValueError, match="TRUSTED_PROXY_HOPS"):
        configuration({"APP_ENV": "testing", "TRUSTED_PROXY_HOPS": hops})


def test_proxy_trust_defaults_to_disabled_and_factory_overrides_shell(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
    assert configuration({"APP_ENV": "testing"})["TRUSTED_PROXY_HOPS"] == 0
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "bad")
    assert configuration({"APP_ENV": "testing", "TRUSTED_PROXY_HOPS": "1"})["TRUSTED_PROXY_HOPS"] == 1

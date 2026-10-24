import pytest
from limits.errors import StorageError
from redis.exceptions import ConnectionError


@pytest.mark.parametrize("path", ["/test-storage", "/api/test-storage"])
@pytest.mark.parametrize("wrapped", [False, True])
def test_storage_outage_is_safe_unavailable(app, client, caplog, path, wrapped):
    diagnostic = "private-rate-limit-driver-diagnostic"

    def unavailable():
        error = ConnectionError(diagnostic)
        raise StorageError(error) if wrapped else error

    app.add_url_rule(path, "unavailable", unavailable)
    result = client.get(path)
    assert result.status_code == 503
    assert diagnostic not in result.get_data(as_text=True)
    assert diagnostic not in caplog.text
    assert "rate_limit_storage_failed" in caplog.text
    if path.startswith("/api/"):
        assert result.json["error"] == "rate_limit_unavailable"

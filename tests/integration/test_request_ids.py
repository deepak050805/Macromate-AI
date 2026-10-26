import re

import pytest


@pytest.mark.parametrize("path,status", [("/health/live", 200), ("/missing", 404), ("/api/tracker/history", 401)])
def test_responses_include_unique_server_generated_request_ids(client, path, status):
    first = client.get(path, headers={"X-Request-ID": "client-controlled-private-value"})
    second = client.get(path)
    assert first.status_code == status
    assert re.fullmatch("[0-9a-f]{32}", first.headers["X-Request-ID"])
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


def test_request_id_is_assigned_before_csrf_rejection(app, client):
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 400
    assert re.fullmatch("[0-9a-f]{32}", response.headers["X-Request-ID"])

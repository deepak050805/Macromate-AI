import pytest


@pytest.mark.parametrize("path", ["/dashboard", "/tracking"])
def test_progress_pages_require_login(client, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", ["/dashboard", "/tracking"])
def test_progress_pages_render(logged_in, path):
    response = logged_in.get(path)
    assert response.status_code == 200
    assert "person@example.test" in response.text or "tracking-form" in response.text
    assert "Log out" in response.text


def test_tracking_assets(logged_in):
    for asset in ("tracking.js", "dashboard.js"):
        assert logged_in.get("/static/js/" + asset).status_code == 200

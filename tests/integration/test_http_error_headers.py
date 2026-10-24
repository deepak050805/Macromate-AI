import pytest
from werkzeug.datastructures import WWWAuthenticate
from werkzeug.exceptions import TooManyRequests, Unauthorized


@pytest.mark.parametrize(
    "method,path,allowed",
    [
        ("post", "/calculator", {"GET", "HEAD", "OPTIONS"}),
        ("get", "/api/auth/login", {"POST", "OPTIONS"}),
    ],
)
def test_method_error_preserves_allow(client, method, path, allowed):
    response = getattr(client, method)(path)
    assert response.status_code == 405
    assert set(response.headers["Allow"].split(", ")) == allowed


@pytest.mark.parametrize("path", ["/test-retry", "/api/test-retry"])
def test_rate_limit_error_preserves_retry_after(app, client, path):
    @app.get(path)
    def retry():
        raise TooManyRequests(description="private diagnostic", retry_after=60)

    response = client.get(path)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert "private diagnostic" not in response.text
    assert int(response.headers["Content-Length"]) == len(response.data)


def test_unauthorized_preserves_multiple_challenges(app, client):
    @app.get("/api/test-challenges")
    def challenges():
        raise Unauthorized(
            www_authenticate=[
                WWWAuthenticate("basic", {"realm": "first"}),
                WWWAuthenticate("bearer", {"realm": "second"}),
            ]
        )

    response = client.get("/api/test-challenges")
    assert response.status_code == 401
    assert len(response.headers.getlist("WWW-Authenticate")) == 2
    assert response.json["message"] == "Please log in to continue"

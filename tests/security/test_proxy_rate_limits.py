import pytest

from app import create_app
from app.extensions import limiter


@pytest.mark.parametrize("hops", [0, 1])
def test_client_limits_follow_only_the_configured_proxy_trust_boundary(hops):
    app = create_app({
        "APP_ENV": "testing", "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "RATELIMIT_STORAGE_URI": "memory://", "RATELIMIT_ENABLED": True,
        "WTF_CSRF_ENABLED": False, "TRUSTED_PROXY_HOPS": hops,
    })

    @app.get("/api/rate-fixture")
    @limiter.limit("2 per minute")
    def limited():
        return {"message": "ok"}

    client = app.test_client()
    for _ in range(2):
        assert client.get("/api/rate-fixture", headers={"X-Forwarded-For": "192.0.2.1"}).status_code == 200
    blocked = client.get("/api/rate-fixture", headers={"X-Forwarded-For": "192.0.2.1"})
    assert blocked.status_code == 429
    # Without explicit proxy trust, changing a header cannot evade the socket limit.
    expected = 200 if hops else 429
    assert client.get("/api/rate-fixture", headers={"X-Forwarded-For": "192.0.2.2"}).status_code == expected
    assert "X-Request-ID" in blocked.headers

import pytest
from flask import jsonify, request

from app import create_app


def proxy_app(hops):
    app = create_app({
        "APP_ENV": "testing", "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "RATELIMIT_ENABLED": False, "TRUSTED_PROXY_HOPS": hops,
    })

    @app.get("/api/proxy-fixture")
    def identity():
        return jsonify(ip=request.remote_addr, scheme=request.scheme, host=request.host, path=request.path)

    return app


@pytest.mark.parametrize("hops,ip,scheme", [(0, "127.0.0.1", "http"), (1, "192.0.2.20", "https"), (2, "192.0.2.10", "http")])
def test_only_explicit_number_of_forwarded_values_is_trusted(hops, ip, scheme):
    response = proxy_app(hops).test_client().get("/api/proxy-fixture", headers={
        "X-Forwarded-For": "192.0.2.10, 192.0.2.20", "X-Forwarded-Proto": "http, https",
        "X-Forwarded-Host": "attacker.invalid", "X-Forwarded-Port": "9999", "X-Forwarded-Prefix": "/attacker",
    })
    assert response.json == {"ip": ip, "scheme": scheme, "host": "localhost", "path": "/api/proxy-fixture"}


def test_too_few_proxy_values_preserves_the_socket_identity():
    response = proxy_app(2).test_client().get("/api/proxy-fixture", headers={
        "X-Forwarded-For": "192.0.2.10", "X-Forwarded-Proto": "https",
    })
    assert response.json["ip"] == "127.0.0.1"
    assert response.json["scheme"] == "http"

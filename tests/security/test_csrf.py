import re


def test_csrf_protection(app, client):
    app.config["WTF_CSRF_ENABLED"] = True
    body = {"weight": 70, "goal": "maintain"}
    assert client.post("/api/macros/calculate", json=body).status_code == 400
    token = re.search(r'name="csrf-token" content="([^"]+)"', client.get("/").text).group(1)
    assert (
        client.post("/api/macros/calculate", json=body, headers={"X-CSRFToken": token}).status_code
        == 200
    )
    stranger = app.test_client()
    assert (
        stranger.post(
            "/api/macros/calculate", json=body, headers={"X-CSRFToken": token}
        ).status_code
        == 400
    )

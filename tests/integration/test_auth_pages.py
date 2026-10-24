import pytest


@pytest.mark.parametrize("path", ["/login", "/signup", "/otp", "/reset-password"])
def test_auth_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert 'type="module"' in response.text
    assert 'name="csrf-token"' in response.text
    assert 'aria-live="polite"' in response.text
    assert 'name="email"' in response.text
    assert "onclick=" not in response.text


def test_password_and_code_fields(client):
    assert 'autocomplete="new-password"' in client.get("/signup").text
    assert 'minlength="12"' in client.get("/signup").text
    assert 'autocomplete="one-time-code"' in client.get("/otp").text
    assert 'autocomplete="new-password"' in client.get("/otp").text
    assert 'name="password"' in client.get("/otp").text
    assert client.get("/static/js/auth.js").status_code == 200

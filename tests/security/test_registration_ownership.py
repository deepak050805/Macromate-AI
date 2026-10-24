import pytest

from app.extensions import db
from app.models import Otp
from app.repositories.users import by_email
from app.services.passwords import verify_password

EMAIL = "owner@example.test"
INITIAL_PASSWORD = "initial unverified password"
OWNER_PASSWORD = "owner selected secure password"


@pytest.fixture
def verification_code(client, monkeypatch):
    sent = []
    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: sent.append(code))
    assert (
        client.post(
            "/api/auth/signup", json={"email": EMAIL, "password": INITIAL_PASSWORD}
        ).status_code
        == 202
    )
    return sent


def test_pre_registered_password_never_becomes_verified(client, verification_code):
    user = by_email(EMAIL)
    db.session.get(Otp, user.id).sent_at = 0
    db.session.commit()
    assert (
        client.post(
            "/api/auth/signup", json={"email": EMAIL, "password": OWNER_PASSWORD}
        ).status_code
        == 202
    )

    response = client.post(
        "/api/auth/verify-otp",
        json={"email": EMAIL, "otp": verification_code[-1], "password": OWNER_PASSWORD},
    )

    assert response.status_code == 200
    assert (
        client.post(
            "/api/auth/login", json={"email": EMAIL, "password": INITIAL_PASSWORD}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login", json={"email": EMAIL, "password": OWNER_PASSWORD}
        ).status_code
        == 200
    )


def test_owner_sets_password_when_proving_email_ownership(client, verification_code):
    response = client.post(
        "/api/auth/verify-otp",
        json={"email": EMAIL, "otp": verification_code[-1], "password": OWNER_PASSWORD},
    )

    assert response.status_code == 200
    user = by_email(EMAIL)
    assert user.is_verified
    assert verify_password(user.password, OWNER_PASSWORD)
    assert not verify_password(user.password, INITIAL_PASSWORD)
    assert db.session.get(Otp, user.id) is None
    assert (
        client.post(
            "/api/auth/verify-otp",
            json={"email": EMAIL, "otp": verification_code[-1], "password": INITIAL_PASSWORD},
        ).status_code
        == 400
    )
    assert verify_password(user.password, OWNER_PASSWORD)


@pytest.mark.parametrize("password", [None, "short", "x" * 129])
def test_verification_requires_valid_password_before_consuming_code(
    client, verification_code, password
):
    response = client.post(
        "/api/auth/verify-otp",
        json={"email": EMAIL, "otp": verification_code[-1], "password": password},
    )

    assert response.status_code == 400
    user = by_email(EMAIL)
    assert not user.is_verified
    assert verify_password(user.password, INITIAL_PASSWORD)
    assert db.session.get(Otp, user.id).attempts == 0


def test_invalid_code_cannot_replace_credentials(client, verification_code):
    response = client.post(
        "/api/auth/verify-otp", json={"email": EMAIL, "otp": "invalid", "password": OWNER_PASSWORD}
    )

    assert response.status_code == 400
    user = by_email(EMAIL)
    assert not user.is_verified
    assert verify_password(user.password, INITIAL_PASSWORD)
    assert db.session.get(Otp, user.id).attempts == 1

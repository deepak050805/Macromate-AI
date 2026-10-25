import re
import smtplib
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.extensions import db
from app.models import Otp, User
from app.services.otp import digest, issue


@pytest.fixture
def mailbox(app, monkeypatch):
    app.config.update(
        MAIL_SERVER="smtp.example.test",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME="mail-account@example.test",
        MAIL_PASSWORD="fictional-mail-password",
        MAIL_DEFAULT_SENDER="sender@example.test",
    )
    mailbox = SimpleNamespace(fail=False, codes=[])
    server = MagicMock()
    server.__enter__.return_value = server

    def deliver(message):
        if mailbox.fail:
            raise smtplib.SMTPException("private-smtp-diagnostic")
        mailbox.codes.append(re.search(r"Your code is ([0-9]{6})", message.get_content())[1])

    server.send_message.side_effect = deliver
    monkeypatch.setattr("app.services.mail.smtplib.SMTP", MagicMock(return_value=server))
    return mailbox


def test_failed_signup_leaves_no_account_and_retry_succeeds(client, mailbox, caplog):
    payload = {"email": "new@example.test", "password": "fictional long password"}
    mailbox.fail = True
    response = client.post("/api/auth/signup", json=payload)
    assert response.status_code == 503
    assert response.json["error"] == "mail_unavailable"
    assert "private-smtp-diagnostic" not in response.get_data(as_text=True) + caplog.text
    assert db.session.scalar(db.select(User).where(User.email == payload["email"])) is None
    assert db.session.scalar(db.select(db.func.count()).select_from(Otp)) == 0

    mailbox.fail = False
    assert client.post("/api/auth/signup", json=payload).status_code == 202
    user = db.session.scalar(db.select(User).where(User.email == payload["email"]))
    assert user is not None
    assert user.is_verified == 0
    assert db.session.get(Otp, user.id).digest == digest(user.id, "verify", mailbox.codes[-1])


@pytest.mark.parametrize(
    ("endpoint", "purpose", "verified"),
    [
        ("/api/auth/signup", "verify", 0),
        ("/api/auth/send-otp", "verify", 0),
        ("/api/auth/request-reset", "reset", 1),
    ],
)
def test_failed_replacement_preserves_challenge_and_allows_retry(
    client, account, mailbox, caplog, endpoint, purpose, verified
):
    account.is_verified = verified
    issue(account, purpose)
    challenge = db.session.get(Otp, account.id)
    challenge.sent_at = time.time() - 120
    challenge.expires_at = time.time() + 3600
    challenge.attempts = 2
    db.session.commit()
    user_id = account.id
    snapshot = (challenge.digest, challenge.purpose, challenge.sent_at, challenge.expires_at, 2)
    credentials = (account.password, account.is_verified, account.auth_version)

    mailbox.fail = True
    payload = {"email": account.email, "password": "fictional replacement password"}
    response = client.post(endpoint, json=payload)
    assert response.status_code == 503
    assert response.json["error"] == "mail_unavailable"
    assert "private-smtp-diagnostic" not in response.get_data(as_text=True) + caplog.text
    db.session.expire_all()
    stored = db.session.get(Otp, user_id)
    assert (
        stored.digest,
        stored.purpose,
        stored.sent_at,
        stored.expires_at,
        stored.attempts,
    ) == snapshot
    assert stored.digest == digest(user_id, purpose, mailbox.codes[0])
    user = db.session.get(User, user_id)
    assert (user.password, user.is_verified, user.auth_version) == credentials

    mailbox.fail = False
    assert client.post(endpoint, json=payload).status_code == 202
    db.session.expire_all()
    replacement = db.session.get(Otp, user_id)
    assert len(mailbox.codes) == 2
    assert replacement.digest == digest(user_id, purpose, mailbox.codes[-1])
    assert replacement.attempts == 0
    assert replacement.sent_at > snapshot[2]
    assert replacement.purpose == purpose
    confirm_path = "/api/auth/reset-password" if purpose == "reset" else "/api/auth/verify-otp"
    response = client.post(confirm_path, json={**payload, "otp": mailbox.codes[-1]})
    assert response.status_code == 200
    assert db.session.get(Otp, user_id) is None

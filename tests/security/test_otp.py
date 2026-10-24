import pytest

from app.extensions import db
from app.models import Otp
from app.services.otp import consume, issue
from app.utils.validation import ValidationError


def test_single_use(account, monkeypatch):
    sent = []
    monkeypatch.setattr("app.services.otp.send_code", lambda email, code: sent.append(code))
    assert issue(account, "verify")
    db.session.commit()
    challenge = db.session.get(Otp, account.id)
    assert sent[0] not in challenge.digest
    assert not issue(account, "verify")
    consume(account, "verify", sent[0])
    db.session.commit()
    with pytest.raises(ValidationError):
        consume(account, "verify", sent[0])


def test_expiry_and_attempts(account, monkeypatch):
    monkeypatch.setattr("app.services.otp.send_code", lambda *args: None)
    issue(account, "verify")
    db.session.commit()
    for _ in range(5):
        with pytest.raises(ValidationError):
            consume(account, "verify", "invalid")
    assert db.session.get(Otp, account.id).attempts == 5
    row = db.session.get(Otp, account.id)
    row.attempts = 0
    row.expires_at = 0
    db.session.commit()
    with pytest.raises(ValidationError):
        consume(account, "verify", "000000")

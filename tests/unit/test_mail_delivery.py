import smtplib
import ssl
from unittest.mock import MagicMock

import pytest

from app.services.mail import DeliveryError, send_code


@pytest.fixture
def smtp(app, monkeypatch):
    app.config.update(
        MAIL_SERVER="smtp.example.test",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME="mail-account@example.test",
        MAIL_PASSWORD="fictional-mail-password",
        MAIL_DEFAULT_SENDER="sender@example.test",
    )
    server = MagicMock()
    server.__enter__.return_value = server
    constructor = MagicMock(return_value=server)
    monkeypatch.setattr("app.services.mail.smtplib.SMTP", constructor)
    return constructor, server


@pytest.mark.parametrize("sender", ["sender@example.test", ""])
def test_delivery_uses_verified_tls_before_authentication(app, smtp, sender):
    constructor, server = smtp
    app.config["MAIL_DEFAULT_SENDER"] = sender
    send_code("recipient@example.test", "123456")
    constructor.assert_called_once_with("smtp.example.test", 587, timeout=10)
    assert [call[0] for call in server.method_calls] == ["starttls", "login", "send_message"]
    context = server.starttls.call_args.kwargs["context"]
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
    server.login.assert_called_once_with("mail-account@example.test", "fictional-mail-password")
    message = server.send_message.call_args.args[0]
    assert message["From"] == (sender or "mail-account@example.test")
    assert message["To"] == "recipient@example.test"
    assert "123456" in message.get_content()
    assert str(app.config["OTP_EXPIRY_SECONDS"]) in message.get_content()


@pytest.mark.parametrize("missing", ["MAIL_USERNAME", "MAIL_PASSWORD"])
def test_incomplete_configuration_never_connects(app, smtp, missing):
    constructor, _ = smtp
    app.config[missing] = ""
    with pytest.raises(DeliveryError, match="^Email delivery is unavailable$"):
        send_code("recipient@example.test", "123456")
    constructor.assert_not_called()


@pytest.mark.parametrize("phase", ["connect", "enter", "starttls", "login", "send_message", "exit"])
def test_transport_failure_has_safe_exception_and_log(smtp, caplog, phase):
    constructor, server = smtp
    diagnostic = "private-smtp-diagnostic fictional-mail-password 123456"
    if phase == "connect":
        constructor.side_effect = TimeoutError(diagnostic)
    else:
        method = {"enter": "__enter__", "exit": "__exit__"}.get(phase, phase)
        getattr(server, method).side_effect = smtplib.SMTPException(diagnostic)
    with pytest.raises(DeliveryError) as caught:
        send_code("recipient@example.test", "123456")
    assert str(caught.value) == "Email delivery is unavailable"
    assert caught.value.__suppress_context__
    assert "mail_delivery_failed" in caplog.text
    assert diagnostic not in caplog.text
    assert "fictional-mail-password" not in caplog.text
    assert "123456" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)
    if phase in {"connect", "enter", "starttls"}:
        server.login.assert_not_called()
    if phase not in {"send_message", "exit"}:
        server.send_message.assert_not_called()

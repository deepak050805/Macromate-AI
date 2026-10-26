"""Outbound formatting failures share the safe mail-unavailable boundary."""

from email.errors import HeaderParseError
from unittest.mock import MagicMock

import pytest

from app.services.mail import DeliveryError, send_code


@pytest.fixture
def isolated_mail(app, monkeypatch, caplog):
    app.config.update(
        MAIL_SERVER="smtp.example.test",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME="fixture@example.test",
        MAIL_PASSWORD="private-mail-credential",
        MAIL_DEFAULT_SENDER="sender@example.test",
    )
    server = MagicMock()
    server.__enter__.return_value = server
    constructor = MagicMock(return_value=server)
    monkeypatch.setattr("app.services.mail.smtplib.SMTP", constructor)
    app.logger.addHandler(caplog.handler)
    try:
        yield constructor, server
    finally:
        app.logger.removeHandler(caplog.handler)


def assert_safe_delivery_error(caught, caplog):
    assert str(caught.value) == "Email delivery is unavailable"
    assert caught.value.__suppress_context__ is True
    assert "mail_delivery_failed" in caplog.text
    assert "private-mail-credential" not in caplog.text
    assert "123456" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


@pytest.mark.parametrize("header", ["sender", "recipient"])
def test_injected_headers_fail_before_opening_a_transport(app, isolated_mail, caplog, header):
    constructor, _ = isolated_mail
    recipient = "recipient@example.test"
    injection = "address@example.test\nBcc: private-mail-credential@example.test"
    if header == "sender":
        app.config["MAIL_DEFAULT_SENDER"] = injection
    else:
        recipient = injection
    with pytest.raises(DeliveryError) as caught:
        send_code(recipient, "123456")
    assert_safe_delivery_error(caught, caplog)
    constructor.assert_not_called()


@pytest.mark.parametrize("phase", ["login", "send_message"])
@pytest.mark.parametrize("encoding_error", [False, True], ids=["invalid-format", "unicode-encoding"])
def test_transport_formatting_errors_do_not_escape_or_log_credentials(
    isolated_mail, caplog, phase, encoding_error
):
    _, server = isolated_mail
    error = (
        UnicodeEncodeError("ascii", "private-mail-credential", 0, 1, "unsupported")
        if encoding_error
        else ValueError("private-mail-credential 123456")
    )
    getattr(server, phase).side_effect = error
    with pytest.raises(DeliveryError) as caught:
        send_code("recipient@example.test", "123456")
    assert_safe_delivery_error(caught, caplog)
    if phase == "login":
        server.send_message.assert_not_called()


def test_header_parser_failure_uses_the_same_safe_boundary(isolated_mail, monkeypatch, caplog):
    constructor, _ = isolated_mail
    monkeypatch.setattr("app.services.mail.EmailMessage", MagicMock(side_effect=HeaderParseError("private-mail-credential")))
    with pytest.raises(DeliveryError) as caught:
        send_code("recipient@example.test", "123456")
    assert_safe_delivery_error(caught, caplog)
    constructor.assert_not_called()


def test_unrelated_programmer_failures_are_not_reclassified_as_delivery_outages(isolated_mail):
    _, server = isolated_mail
    server.login.side_effect = RuntimeError("unexpected-mail-implementation-defect")
    with pytest.raises(RuntimeError, match="unexpected-mail-implementation-defect"):
        send_code("recipient@example.test", "123456")

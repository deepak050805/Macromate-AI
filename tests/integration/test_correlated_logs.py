import io
import json
import logging
from unittest.mock import Mock

from sqlalchemy.exc import SQLAlchemyError

from app.logging_config import EventFormatter


def test_failure_event_matches_response_without_including_credentials(app, logged_in, monkeypatch):
    stream = io.StringIO()
    app.logger.handlers[0].setStream(stream)
    monkeypatch.setattr("app.security.by_id", Mock(side_effect=SQLAlchemyError("private-driver-secret")))
    response = logged_in.get("/api/tracker/history?email=private@example.test")
    event = json.loads(stream.getvalue().splitlines()[-1])
    assert response.status_code == 503
    assert event["event"] == "database_request_failed"
    assert event["request_id"] == response.headers["X-Request-ID"]
    assert "private" not in stream.getvalue()


def test_formatter_can_emit_operator_events_without_a_request():
    record = logging.LogRecord("operator", logging.INFO, "", 0, "account_promoted", (), None)
    event = json.loads(EventFormatter().format(record))
    assert event == {"level": "INFO", "logger": "operator", "event": "account_promoted"}

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import User

DRIVER_DETAIL = "private-database-driver-diagnostic"


@pytest.mark.parametrize("path", ["/dashboard", "/tracking", "/calculator", "/login", "/"])
def test_database_outage_renders_safe_html(logged_in, monkeypatch, caplog, path):
    lookup = Mock(side_effect=SQLAlchemyError(DRIVER_DETAIL))
    monkeypatch.setattr("app.security.by_id", lookup)

    response = logged_in.get(path)

    assert response.status_code == 503
    assert response.mimetype == "text/html"
    assert b"Service temporarily unavailable" in response.data
    assert DRIVER_DETAIL not in response.text
    assert DRIVER_DETAIL not in caplog.text
    assert "database_request_failed" in caplog.text
    assert lookup.call_count == 1


@pytest.mark.parametrize(
    "method,path,status", [("get", "/missing-page", 404), ("post", "/dashboard", 405)]
)
def test_http_error_page_does_not_query_account(logged_in, monkeypatch, method, path, status):
    lookup = Mock(side_effect=SQLAlchemyError(DRIVER_DETAIL))
    monkeypatch.setattr("app.security.by_id", lookup)

    response = getattr(logged_in, method)(path)

    assert response.status_code == status
    assert response.mimetype == "text/html"
    lookup.assert_not_called()


def test_identity_lookup_recovers_on_next_request(logged_in, monkeypatch):
    with monkeypatch.context() as outage:
        outage.setattr("app.security.by_id", Mock(side_effect=SQLAlchemyError(DRIVER_DETAIL)))
        assert logged_in.get("/dashboard").status_code == 503

    response = logged_in.get("/dashboard")

    assert response.status_code == 200
    assert b'id="logout"' in response.data


def test_api_database_error_rolls_back_without_leaking_details(logged_in, monkeypatch, caplog):
    db.session.add(User(email="uncommitted@example.test", password="!reset-required"))
    monkeypatch.setattr("app.security.by_id", Mock(side_effect=SQLAlchemyError(DRIVER_DETAIL)))

    response = logged_in.get("/api/tracker/history")

    assert response.status_code == 503
    assert response.json == {
        "message": "Service temporarily unavailable",
        "error": "database_unavailable",
    }
    assert DRIVER_DETAIL not in response.text
    assert DRIVER_DETAIL not in caplog.text
    assert (
        db.session.scalar(db.select(User).where(User.email == "uncommitted@example.test")) is None
    )

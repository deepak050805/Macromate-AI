import csv
import io
from datetime import date

import pytest

from app.extensions import db
from app.models import Progress, User


@pytest.fixture
def dated_entries(account):
    db.session.add(User(email="other-filter@example.test", password="!disabled", is_verified=1))
    db.session.flush()
    db.session.add_all([
        Progress(email=account.email, weight=70, calories=2000, record_date=date(2024, 1, 1)),
        Progress(email=account.email, weight=71, calories=2100, record_date=date(2024, 1, 15)),
        Progress(email=account.email, weight=72, calories=2200, record_date=date(2024, 2, 1)),
        Progress(email=account.email, weight=69, calories=1900, record_date=None),
        Progress(email="other-filter@example.test", weight=99, calories=2500, record_date=date(2024, 1, 15)),
    ])
    db.session.commit()


@pytest.mark.parametrize("query,weights", [
    ("", [72, 71, 70, 69]),
    ("?date_from=2024-01-15", [72, 71]),
    ("?date_to=2024-01-15", [71, 70]),
    ("?date_from=2024-01-15&date_to=2024-02-01", [72, 71]),
    ("?date_from=2024-01-15&date_to=2024-01-15", [71]),
])
def test_history_range_is_inclusive_and_owner_scoped(logged_in, dated_entries, query, weights):
    response = logged_in.get("/api/tracker/history" + query)
    assert response.status_code == 200
    assert [record["weight"] for record in response.json["records"]] == weights
    assert response.json["total"] == len(weights)


@pytest.mark.parametrize("query", [
    "date_from=invalid", "date_to=2024-02-30", "date_from=1999-01-01",
    "date_to=9999-01-01", "date_from=2024-02-01&date_to=2024-01-01",
])
def test_invalid_history_ranges_return_safe_validation_errors(logged_in, query):
    response = logged_in.get("/api/tracker/history?" + query)
    assert response.status_code == 400
    assert response.json["error"] == "validation_error"


def test_csv_export_contains_only_owned_records_and_retains_unknown_dates(logged_in, dated_entries):
    response = logged_in.get("/api/tracker/export.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    assert response.headers["Cache-Control"] == "no-store"
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert [float(row["weight_kg"]) for row in rows] == [72, 71, 70, 69]
    assert rows[-1]["date_utc"] == ""


def test_csv_export_uses_the_same_inclusive_range(logged_in, dated_entries):
    response = logged_in.get("/api/tracker/export.csv?date_from=2024-01-15&date_to=2024-01-15")
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 1
    assert float(rows[0]["weight_kg"]) == 71


def test_csv_limit_returns_an_error_instead_of_silently_truncating(logged_in, dated_entries, monkeypatch):
    monkeypatch.setattr("app.routes.tracking.EXPORT_LIMIT", 1)
    response = logged_in.get("/api/tracker/export.csv")
    assert response.status_code == 400
    assert response.json["error"] == "validation_error"
    assert "narrower date range" in response.json["message"]
    assert "Content-Disposition" not in response.headers


def test_csv_export_requires_authentication(client):
    assert client.get("/api/tracker/export.csv").status_code == 401


def test_progress_summary_is_owned_and_excludes_undated_rows_from_change(logged_in, dated_entries):
    response = logged_in.get("/api/tracker/summary")
    assert response.status_code == 200
    assert response.json == {
        "total": 4, "dated": 3, "average_weight": 70.5, "average_calories": 2050.0,
        "first_date": "2024-01-01", "last_date": "2024-02-01", "weight_change": 2.0,
    }


def test_single_dated_record_does_not_claim_a_weight_change(logged_in, dated_entries):
    response = logged_in.get("/api/tracker/summary?date_from=2024-01-15&date_to=2024-01-15")
    assert response.json["total"] == 1
    assert response.json["average_weight"] == 71
    assert response.json["weight_change"] is None


def test_empty_progress_summary_has_null_estimates(logged_in):
    response = logged_in.get("/api/tracker/summary")
    assert response.json["total"] == response.json["dated"] == 0
    assert response.json["average_weight"] is None
    assert response.json["average_calories"] is None
    assert response.json["weight_change"] is None


def test_summary_requires_authentication(client):
    assert client.get("/api/tracker/summary").status_code == 401

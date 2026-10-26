from datetime import date

import pytest

from app.extensions import db
from app.models import Progress, User


@pytest.fixture
def dated_entries(account):
    db.session.add(User(email="other-filter@example.test", password="!disabled", is_verified=1))
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

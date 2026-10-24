from datetime import date

from app.extensions import db
from app.models import Progress


def test_undated_legacy_entries_follow_dated_entries(logged_in, account):
    db.session.add_all(
        [
            Progress(email=account.email, weight=70, calories=2000, record_date=None),
            Progress(email=account.email, weight=71, calories=2100, record_date=date(2024, 1, 1)),
        ]
    )
    db.session.commit()
    records = logged_in.get("/api/tracker/history").json["records"]
    assert [record["date"] for record in records] == ["2024-01-01", None]

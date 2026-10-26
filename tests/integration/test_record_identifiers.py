from unittest.mock import Mock

import pytest

from app.extensions import db
from app.models import Progress


@pytest.mark.parametrize("record_id", [0, 2**31, 10**100])
@pytest.mark.parametrize("method", ["put", "delete"])
def test_unrepresentable_record_ids_are_not_found_without_querying_records(logged_in, monkeypatch, record_id, method):
    query = Mock(side_effect=AssertionError("out-of-range record ID reached the database"))
    # Authentication loads User through Session.get; a Progress scalar lookup is unnecessary.
    with monkeypatch.context() as guard:
        guard.setattr(db.session, "scalar", query)
        response = getattr(logged_in, method)(f"/api/tracker/{record_id}", json={
            "weight": 70, "calories": 2000, "date": "2024-01-01",
        })
    assert response.status_code == 404
    query.assert_not_called()
    assert db.session.scalar(db.select(db.func.count(Progress.id))) == 0

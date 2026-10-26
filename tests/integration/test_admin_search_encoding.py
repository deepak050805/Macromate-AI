from unittest.mock import Mock

import pytest

from app.extensions import db


@pytest.mark.parametrize("query", ["person\x00", "person\x01", "person\x7f"])
def test_admin_search_rejects_control_characters_before_record_query(logged_in, account, monkeypatch, query):
    account.role = "admin"
    db.session.commit()
    listing = Mock(side_effect=AssertionError("invalid search reached SQL"))
    monkeypatch.setattr("app.routes.admin.listing", listing)
    response = logged_in.get("/api/auth/all-users", query_string={"q": query})
    assert response.status_code == 400
    assert response.json["error"] == "validation_error"
    listing.assert_not_called()

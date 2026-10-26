from unittest.mock import Mock

import pytest


@pytest.mark.parametrize("identity,version", [
    (True, 1), ("1", 1), ({"id": 1}, 1), ([1], 1), (0, 1), (-1, 1), (2**31, 1),
    (1, None), (1, True), (1, "1"), (1, 0),
])
def test_malformed_signed_identity_is_cleared_before_database_access(client, monkeypatch, identity, version):
    with client.session_transaction() as session:
        session["user_id"] = identity
        session["auth_version"] = version
    lookup = Mock(side_effect=AssertionError("malformed session reached SQL"))
    monkeypatch.setattr("app.security.by_id", lookup)
    response = client.get("/api/tracker/history")
    assert response.status_code == 401
    lookup.assert_not_called()
    with client.session_transaction() as session:
        assert "user_id" not in session

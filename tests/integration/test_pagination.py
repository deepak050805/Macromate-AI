import pytest

from app.extensions import db


@pytest.mark.parametrize(
    "endpoint",
    ["/api/tracker/history", "/api/tracker/get/person@example.test", "/api/auth/all-users"],
)
def test_oversized_page_returns_validation_error(logged_in, account, endpoint):
    account.role = "admin"
    db.session.commit()

    response = logged_in.get(endpoint, query_string={"page": "9" * 5000})

    assert response.status_code == 400
    assert response.json == {
        "error": "validation_error",
        "message": "Page must be between 1 and 10000",
    }

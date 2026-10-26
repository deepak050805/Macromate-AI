import pytest

from app.extensions import db
from app.models import User


@pytest.fixture
def searchable_accounts(account):
    account.role = "admin"
    db.session.add_all([
        User(email="alpha@example.test", password="!disabled", is_verified=1),
        User(email="beta@example.test", password="!disabled", is_verified=0),
        User(email="under_score@other.test", password="!disabled", is_verified=0),
        User(email="percent%tag@example.test", password="!disabled", is_verified=1),
    ])
    db.session.commit()


@pytest.mark.parametrize("query,email", [("ALPHA", "alpha@example.test"),
    ("_", "under_score@other.test"), ("%", "percent%tag@example.test")])
def test_admin_search_is_case_insensitive_and_treats_wildcards_literally(logged_in, searchable_accounts, query, email):
    response = logged_in.get("/api/auth/all-users", query_string={"q": query})
    assert response.status_code == 200
    assert [user["email"] for user in response.json["users"]] == [email]


@pytest.mark.parametrize("state,count", [("all", 5), ("verified", 3), ("pending", 2)])
def test_admin_verification_filter(logged_in, searchable_accounts, state, count):
    response = logged_in.get("/api/auth/all-users", query_string={"verification": state})
    assert response.status_code == 200
    assert response.json["total"] == count


def test_admin_search_remains_forbidden_to_regular_accounts(logged_in):
    assert logged_in.get("/api/auth/all-users?q=person").status_code == 403


def test_admin_filter_validation_is_bounded(logged_in, searchable_accounts):
    assert logged_in.get("/api/auth/all-users", query_string={"q": "a" * 255}).status_code == 400
    assert logged_in.get("/api/auth/all-users?verification=unknown").status_code == 400

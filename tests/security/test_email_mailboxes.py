from unittest.mock import Mock

import pytest

from app.utils.validation import ValidationError, email_value


@pytest.mark.parametrize("email", ["name<person@example.test>", "person@example.test,other", "a..b@example.test", "a@example..test"])
def test_email_is_one_mailbox_not_an_smtp_recipient_list(email):
    with pytest.raises(ValidationError, match="valid email"):
        email_value(email)


@pytest.mark.parametrize("path", ["signup", "login", "request-reset", "send-otp"])
def test_malformed_mailbox_is_rejected_before_account_lookup(client, monkeypatch, path):
    lookup = Mock(side_effect=AssertionError("invalid mailbox reached account storage"))
    monkeypatch.setattr("app.services.auth.by_email", lookup)
    response = client.post(f"/api/auth/{path}", json={
        "email": "person@example.test,other", "password": "fictional signup password",
    })
    assert response.status_code == 400
    lookup.assert_not_called()


def test_supported_address_tags_and_hyphenated_domains_are_retained():
    assert email_value("Person+tag@Example-Domain.test") == "person+tag@example-domain.test"

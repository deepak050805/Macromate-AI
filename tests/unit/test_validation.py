import pytest

from app.utils.validation import (
    ValidationError,
    email_value,
    page_number,
    password_value,
    record_date,
)


def test_normalization():
    assert email_value(" Person@Example.test ") == "person@example.test"
    assert record_date("2024-02-29").isoformat() == "2024-02-29"
    assert page_number("1") == 1


@pytest.mark.parametrize(
    "value", [None, [], "abc", "a@b", "a b@example.test", "a@b@c.test", "a\n@example.test"]
)
def test_bad_email(value):
    with pytest.raises(ValidationError):
        email_value(value)


@pytest.mark.parametrize("control", ["\x00", "\x01", "\x1b", "\x7f", "\ud800", "\udfff"])
def test_email_rejects_non_text_characters_before_storage_or_delivery(control):
    with pytest.raises(ValidationError, match="valid email"):
        email_value(f"person{control}@example.test")


@pytest.mark.parametrize(
    "value", [None, True, "2024-02-30", "9999-01-01", "1999-01-01", "20240101"]
)
def test_bad_date(value):
    with pytest.raises(ValidationError):
        record_date(value)


@pytest.mark.parametrize("value", [None, "short", "x" * 129])
def test_bad_password(value):
    with pytest.raises(ValidationError):
        password_value(value)


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "1.2",
        "10001",
        "all",
        None,
        True,
        1,
        [],
        pytest.param("9" * 5000, id="oversized-decimal"),
    ],
)
def test_bad_page(value):
    with pytest.raises(ValidationError):
        page_number(value)


@pytest.mark.parametrize(
    ("value", "expected"), [("1", 1), ("10000", 10000), ("00001", 1), ("\u0661\u0662", 12)]
)
def test_valid_page(value, expected):
    assert page_number(value) == expected

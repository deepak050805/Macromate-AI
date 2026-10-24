import pytest
from app.utils.validation import ValidationError,email_value,password_value,record_date,page_number


def test_normalization():
    assert email_value(" Person@Example.test ") == "person@example.test"
    assert record_date("2024-02-29").isoformat() == "2024-02-29"
    assert page_number("1") == 1


@pytest.mark.parametrize("value", [None,[],"abc","a@b","a b@example.test","a@b@c.test","a\n@example.test"])
def test_bad_email(value):
    with pytest.raises(ValidationError): email_value(value)


@pytest.mark.parametrize("value", [None,True,"2024-02-30","9999-01-01","1999-01-01","20240101"])
def test_bad_date(value):
    with pytest.raises(ValidationError): record_date(value)


@pytest.mark.parametrize("value", [None,"short","x"*129])
def test_bad_password(value):
    with pytest.raises(ValidationError): password_value(value)


@pytest.mark.parametrize("value", ["0","-1","1.2","10001","all"])
def test_bad_page(value):
    with pytest.raises(ValidationError): page_number(value)

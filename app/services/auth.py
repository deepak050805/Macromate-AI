from flask import session
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.repositories.users import by_email
from app.services.otp import consume, issue
from app.services.passwords import hash_password, verify_password
from app.utils.validation import ValidationError, email_value, password_value

NOTICE = "If the account is eligible, a verification code has been sent."
_DUMMY_PASSWORD_HASH = hash_password("placeholder that never owns an account")


def signup(data):
    email = email_value(data.get("email"))
    password = password_value(data.get("password"))
    user = by_email(email, lock=True)
    if user and user.is_verified:
        return NOTICE
    if not user:
        user = User(email=email, password=hash_password(password))
        db.session.add(user)
        try:
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            return NOTICE
    issue(user, "verify")
    db.session.commit()
    return NOTICE


def login(data):
    email = email_value(data.get("email"))
    password = data.get("password")
    if not isinstance(password, str) or len(password) > 128:
        raise ValidationError("Invalid credentials")
    user = by_email(email)
    matches = verify_password(user.password if user else _DUMMY_PASSWORD_HASH, password)
    if not user or not matches or not user.is_verified:
        return None
    session.clear()
    session.permanent = True
    session["user_id"] = user.id
    session["auth_version"] = user.auth_version
    return user


def request_code(data, purpose):
    user = by_email(email_value(data.get("email")), lock=True)
    if user and (purpose == "reset" or not user.is_verified):
        issue(user, purpose)
        db.session.commit()
    return NOTICE


def confirm(data, purpose):
    user = by_email(email_value(data.get("email")), lock=True)
    password = password_value(data.get("password"))
    consume(user, purpose, data.get("otp"))
    user.is_verified = 1
    user.password = hash_password(password)
    user.auth_version += 1
    session.clear()
    db.session.commit()

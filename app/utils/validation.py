import math
import re
from datetime import date, datetime, timezone
from flask import request


class ValidationError(ValueError):
    pass


def payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("A JSON object is required")
    return data


def email_value(value):
    if not isinstance(value, str):
        raise ValidationError("Enter a valid email address")
    value = value.strip().lower()
    if len(value) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValidationError("Enter a valid email address")
    return value


def password_value(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 128:
        raise ValidationError("Password must contain 12 to 128 characters")
    return value


def number(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValidationError(f"{name} must be a number")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        raise ValidationError(f"{name} must be a number") from None
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValidationError(f"{name} must be between {minimum} and {maximum}")
    return result


def record_date(value):
    if not isinstance(value, str):
        raise ValidationError("Date must use YYYY-MM-DD")
    try:
        result = date.fromisoformat(value)
    except ValueError:
        raise ValidationError("Date must use YYYY-MM-DD") from None
    if result.isoformat() != value or result > datetime.now(timezone.utc).date() or result.year < 2000:
        raise ValidationError("Date must be between 2000-01-01 and today (UTC)")
    return result


def page_number(value):
    if not isinstance(value, str) or not value.isdecimal() or not 1 <= int(value) <= 10000:
        raise ValidationError("Page must be between 1 and 10000")
    return int(value)

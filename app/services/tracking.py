from app.extensions import db
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Conflict
from app.models import Progress
from app.repositories.progress import owned, summary
from app.utils.validation import ValidationError, number, record_date, request_key_value


def values(data):
    weight = number(data.get("weight"), "Weight (kg)", 1, 500)
    calories = number(data.get("calories"), "Calories", 0, 20000)
    if not calories.is_integer():
        raise ValidationError("Calories must be a whole number")
    return {
        "weight": weight,
        "calories": int(calories),
        "record_date": record_date(data.get("date")),
    }


def save(email, data, record_id=None):
    fields = values(data)
    key = request_key_value(data.get("request_key")) if record_id is None else None
    if key:
        existing = _request_record(email, key)
        if existing is not None:
            return _matching_request(existing, fields)
    record = owned(record_id, email) if record_id is not None else Progress(email=email)
    if record is None:
        return None
    if record_id is None:
        record.request_key = key
    for key, value in fields.items():
        setattr(record, key, value)
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if key:
            existing = _request_record(email, key)
            if existing is not None:
                return _matching_request(existing, fields)
        raise
    return record


def _request_record(email, key):
    return db.session.scalar(db.select(Progress).where(
        Progress.email == email, Progress.request_key == key,
    ))


def _matching_request(record, fields):
    if any(getattr(record, key) != value for key, value in fields.items()):
        raise Conflict()
    return record


def delete(email, record_id):
    record = owned(record_id, email)
    if not record:
        return False
    db.session.delete(record)
    db.session.commit()
    return True


def summarize(email, date_from=None, date_to=None):
    result = summary(email, date_from, date_to)
    for key in ("average_weight", "average_calories", "weight_change"):
        if result[key] is not None:
            result[key] = round(float(result[key]), 2)
    for key in ("first_date", "last_date"):
        if result[key] is not None:
            result[key] = result[key].isoformat()
    return result

from app.extensions import db
from app.models import Progress
from app.repositories.progress import owned
from app.utils.validation import ValidationError, number, record_date


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
    record = owned(record_id, email) if record_id else Progress(email=email)
    if record is None:
        return None
    for key, value in fields.items():
        setattr(record, key, value)
    db.session.add(record)
    db.session.commit()
    return record


def delete(email, record_id):
    record = owned(record_id, email)
    if not record:
        return False
    db.session.delete(record)
    db.session.commit()
    return True

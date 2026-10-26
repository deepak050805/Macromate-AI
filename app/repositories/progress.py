from app.extensions import db
from app.models import Progress


def owned(record_id, email):
    return db.session.scalar(
        db.select(Progress).where(Progress.id == record_id, Progress.email == email)
    )


def query_for_owner(email, date_from=None, date_to=None):
    query = (
        db.select(Progress)
        .where(Progress.email == email)
        .order_by(Progress.record_date.desc().nullslast(), Progress.id.desc())
    )
    if date_from is not None:
        query = query.where(Progress.record_date >= date_from)
    if date_to is not None:
        query = query.where(Progress.record_date <= date_to)
    return query


def history(email, page=1, date_from=None, date_to=None):
    return db.paginate(
        query_for_owner(email, date_from, date_to), page=page, per_page=20, error_out=False
    )

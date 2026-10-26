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


def summary(email, date_from=None, date_to=None):
    source = query_for_owner(email, date_from, date_to).order_by(None).subquery()
    dated = db.func.count(source.c.record_date)
    first_weight = db.select(source.c.weight).where(
        source.c.record_date.is_not(None)
    ).order_by(source.c.record_date, source.c.id).limit(1).correlate(None).scalar_subquery()
    last_weight = db.select(source.c.weight).where(
        source.c.record_date.is_not(None)
    ).order_by(source.c.record_date.desc(), source.c.id.desc()).limit(1).correlate(None).scalar_subquery()
    # One statement gives aggregates and edge values the same database snapshot.
    count, dated_count, weight, calories, first_date, last_date, change = db.session.execute(db.select(
        db.func.count(source.c.id), dated,
        db.func.avg(source.c.weight), db.func.avg(source.c.calories),
        db.func.min(source.c.record_date), db.func.max(source.c.record_date),
        db.case((dated >= 2, last_weight - first_weight), else_=None),
    )).one()
    return {
        "total": count, "dated": dated_count,
        "average_weight": weight, "average_calories": calories,
        "first_date": first_date, "last_date": last_date, "weight_change": change,
    }

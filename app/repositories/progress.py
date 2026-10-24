from app.extensions import db
from app.models import Progress


def owned(record_id, email):
    return db.session.scalar(
        db.select(Progress).where(Progress.id == record_id, Progress.email == email)
    )


def history(email, page=1):
    query = (
        db.select(Progress)
        .where(Progress.email == email)
        .order_by(Progress.record_date.desc().nullslast(), Progress.id.desc())
    )
    return db.paginate(query, page=page, per_page=20, error_out=False)

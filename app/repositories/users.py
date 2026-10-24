"""Parameterized SQLAlchemy account access; callers own transactions."""
from app.extensions import db
from app.models import User


def by_email(email, lock=False):
    query = db.select(User).where(User.email == email)
    if lock:
        query = query.with_for_update()
    return db.session.scalar(query)


def by_id(user_id):
    return db.session.get(User, user_id)


def listing(page, per_page=25):
    return db.paginate(db.select(User).order_by(User.id), page=page, per_page=per_page, error_out=False)

"""Parameterized SQLAlchemy account access; callers own transactions."""

from app.extensions import db
from app.models import User


def by_email(email, lock=False):
    query = db.select(User).where(User.email == email)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    return db.session.scalar(query)


def by_id(user_id, lock=False):
    if lock:
        return db.session.scalar(db.select(User).where(User.id == user_id).with_for_update().execution_options(populate_existing=True))
    return db.session.get(User, user_id)


def listing(page, per_page=25, search=None, verified=None):
    query = db.select(User).order_by(User.id)
    if search:
        query = query.where(db.func.lower(User.email).contains(search.lower(), autoescape=True))
    if verified is not None:
        query = query.where(User.is_verified == int(verified))
    return db.paginate(query, page=page, per_page=per_page, error_out=False)

from functools import wraps

from flask import abort, session

from app.repositories.users import by_id


def current_user():
    user_id = session.get("user_id")
    version = session.get("auth_version")
    if user_id is not None and (
        type(user_id) is not int or not 1 <= user_id <= 2_147_483_647
        or type(version) is not int or version < 1
    ):
        session.clear()
        return None
    user = by_id(user_id) if user_id else None
    if session.get("user_id") and (
        not user or not user.is_verified or user.auth_version != session.get("auth_version")
    ):
        session.clear()
        return None
    return user


def authenticated(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user():
            abort(401)
        return view(*args, **kwargs)

    return wrapper


def administrator(view):
    @wraps(view)
    @authenticated
    def wrapper(*args, **kwargs):
        if current_user().role != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapper

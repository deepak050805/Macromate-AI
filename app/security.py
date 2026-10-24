from functools import wraps
from flask import abort, g, session
from app.repositories.users import by_id


def current_user():
    if "user" not in g:
        user = by_id(session["user_id"]) if session.get("user_id") else None
        if user and (not user.is_verified or user.auth_version != session.get("auth_version")):
            user = None
        g.user = user
    return g.user


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

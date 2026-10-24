from flask import Blueprint, abort, jsonify, session

from app.extensions import limiter
from app.services import auth
from app.utils.validation import payload

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/signup")
@limiter.limit("5 per minute; 20 per hour")
def signup():
    return jsonify(message=auth.signup(payload())), 202


@bp.post("/login")
@limiter.limit("5 per minute; 20 per hour")
def login():
    user = auth.login(payload())
    if not user:
        abort(401)
    return jsonify(message="Login successful", email=user.email, role=user.role)


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out")


@bp.post("/send-otp")
@limiter.limit("3 per minute; 10 per hour")
def resend():
    return jsonify(message=auth.request_code(payload(), "verify")), 202


@bp.post("/verify-otp")
@limiter.limit("10 per minute")
def verify():
    auth.confirm(payload(), "verify")
    return jsonify(message="OTP verified")


@bp.post("/request-reset")
@limiter.limit("3 per minute; 10 per hour")
def request_reset():
    return jsonify(message=auth.request_code(payload(), "reset")), 202


@bp.post("/reset-password")
@limiter.limit("10 per minute")
def reset():
    auth.confirm(payload(), "reset")
    return jsonify(message="Password updated. Please log in.")

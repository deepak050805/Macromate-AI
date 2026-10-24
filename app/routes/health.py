from flask import Blueprint, jsonify
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db, limiter
from app.models import Otp, Progress, User

bp = Blueprint("health", __name__)


@bp.get("/health/live")
@limiter.exempt
def live():
    return jsonify(status="ok")


@bp.get("/health/ready")
@limiter.exempt
def ready():
    try:
        for model in (User, Progress, Otp):
            db.session.execute(db.select(model).limit(0)).close()
        return jsonify(status="ok")
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(status="unavailable"), 503

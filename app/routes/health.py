from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db, limiter

bp = Blueprint("health", __name__)


@bp.get("/health/live")
@limiter.exempt
def live():
    return jsonify(status="ok")


@bp.get("/health/ready")
@limiter.exempt
def ready():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok")
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(status="unavailable"), 503

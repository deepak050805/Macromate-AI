from flask import Blueprint, jsonify

from app.services.nutrition import calculate
from app.utils.validation import payload

bp = Blueprint("calculator", __name__, url_prefix="/api/macros")


@bp.post("/calculate")
def calculate_macros():
    return jsonify(calculate(payload()))

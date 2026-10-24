from flask import Blueprint, abort, jsonify, request
from app.repositories.progress import history
from app.security import authenticated, current_user
from app.services import tracking
from app.utils.validation import page_number, payload

bp = Blueprint("tracking", __name__, url_prefix="/api/tracker")


@bp.post("/add")
@authenticated
def add():
    record = tracking.save(current_user().email, payload())
    return jsonify(message="Saved", record=record.as_dict()), 201


@bp.get("/history")
@authenticated
def get_history():
    records = history(current_user().email, page_number(request.args.get("page", "1")))
    return jsonify(records=[record.as_dict() for record in records.items], page=records.page, pages=records.pages, total=records.total)


@bp.get("/get/<path:email>")
@authenticated
def legacy_history(email):
    if email != current_user().email:
        abort(403)
    return get_history()


@bp.put("/<int:record_id>")
@authenticated
def update(record_id):
    record = tracking.save(current_user().email, payload(), record_id)
    if record is None:
        abort(404)
    return jsonify(message="Updated", record=record.as_dict())


@bp.delete("/<int:record_id>")
@authenticated
def delete(record_id):
    if not tracking.delete(current_user().email, record_id):
        abort(404)
    return jsonify(message="Deleted")

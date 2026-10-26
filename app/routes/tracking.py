import csv
import io

from flask import Blueprint, Response, abort, jsonify, request

from app.extensions import db
from app.repositories.progress import history, query_for_owner
from app.security import authenticated, current_user
from app.services import tracking
from app.utils.validation import ValidationError, date_range, page_number, payload

bp = Blueprint("tracking", __name__, url_prefix="/api/tracker")
EXPORT_LIMIT = 10000


@bp.post("/add")
@authenticated
def add():
    record = tracking.save(current_user().email, payload())
    return jsonify(message="Saved", record=record.as_dict()), 201


@bp.get("/history")
@authenticated
def get_history():
    start, end = date_range(request.args)
    records = history(current_user().email, page_number(request.args.get("page", "1")), start, end)
    return jsonify(
        records=[record.as_dict() for record in records.items],
        page=records.page,
        pages=records.pages,
        total=records.total,
    )


@bp.get("/get/<path:email>")
@authenticated
def legacy_history(email):
    if email != current_user().email:
        abort(403)
    return get_history()


@bp.get("/export.csv")
@authenticated
def export_csv():
    start, end = date_range(request.args)
    records = db.session.scalars(
        query_for_owner(current_user().email, start, end).limit(EXPORT_LIMIT + 1)
    ).all()
    if len(records) > EXPORT_LIMIT:
        raise ValidationError(
            f"Export is limited to {EXPORT_LIMIT} records. Select a narrower date range."
        )
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["date_utc", "weight_kg", "calories_kcal"])
    for record in records:
        writer.writerow([
            record.record_date.isoformat() if record.record_date else "",
            float(record.weight), int(record.calories),
        ])
    return Response(
        output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=macromate-progress.csv"},
    )


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

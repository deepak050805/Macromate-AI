from flask import Blueprint, jsonify, request
from app.repositories.users import listing
from app.security import administrator
from app.utils.validation import page_number

bp = Blueprint("admin", __name__, url_prefix="/api/auth")


@bp.get("/all-users")
@administrator
def users():
    records = listing(page_number(request.args.get("page", "1")))
    return jsonify(users=[{"id": u.id, "email": u.email, "verified": bool(u.is_verified)} for u in records.items], page=records.page, pages=records.pages, total=records.total)

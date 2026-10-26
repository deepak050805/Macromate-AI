from flask import Blueprint, jsonify, request

from app.repositories.users import listing
from app.security import administrator
from app.utils.validation import ValidationError, page_number

bp = Blueprint("admin", __name__, url_prefix="/api/auth")


@bp.get("/all-users")
@administrator
def users():
    search = request.args.get("q", "").strip()
    if len(search) > 254:
        raise ValidationError("Email search is limited to 254 characters")
    state = request.args.get("verification", "all")
    if state not in ("all", "verified", "pending"):
        raise ValidationError("Choose all, verified or pending accounts")
    records = listing(
        page_number(request.args.get("page", "1")), search=search,
        verified=None if state == "all" else state == "verified",
    )
    return jsonify(
        users=[
            {"id": u.id, "email": u.email, "verified": bool(u.is_verified)} for u in records.items
        ],
        page=records.page,
        pages=records.pages,
        total=records.total,
    )

from flask import Blueprint, request, jsonify
from backend.models import connect

tracker_bp = Blueprint("tracker", __name__)

@tracker_bp.route("/add", methods=["POST"])
def add():
    data = request.json
    email = data["email"]
    weight = data["weight"]
    calories = data["calories"]

    conn = connect()
    c = conn.cursor()

    c.execute("INSERT INTO progress (email, weight, calories) VALUES (?, ?, ?)",
              (email, weight, calories))
    conn.commit()

    return jsonify({"message": "Saved"})

@tracker_bp.route("/get/<email>", methods=["GET"])
def get(email):
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT weight, calories FROM progress WHERE email=?", (email,))
    data = c.fetchall()

    return jsonify(data)
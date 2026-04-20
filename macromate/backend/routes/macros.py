from flask import Blueprint, request, jsonify

macros_bp = Blueprint("macros", __name__)

@macros_bp.route("/calculate", methods=["POST"])
def calculate_macros():
    data = request.json

    weight = float(data["weight"])
    goal = data["goal"]

    maintenance = weight * 2.2 * 15

    if goal == "fat_loss":
        calories = maintenance * 0.9
    elif goal == "gain":
        calories = maintenance * 1.1
    else:
        calories = maintenance

    protein = weight * 2
    fats = weight * 0.8
    carbs = (calories - (protein*4 + fats*9)) / 4

    return jsonify({
        "calories": int(calories),
        "protein": int(protein),
        "carbs": int(carbs),
        "fats": int(fats)
    })
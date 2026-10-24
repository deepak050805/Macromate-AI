"""Preserve the original weight-based energy and macro formulas."""
from app.utils.validation import ValidationError, number


def calculate(data):
    weight = number(data.get("weight"), "Weight (kg)", 30, 350)
    goal = data.get("goal")
    factors = {"fat_loss": 0.9, "maintain": 1.0, "gain": 1.1}
    if not isinstance(goal, str) or goal not in factors:
        raise ValidationError("Choose fat_loss, maintain or gain")
    calories = round(weight * 2.2 * 15 * factors[goal], 2)
    protein = round(weight * 2, 2)
    fats = round(weight * 0.8, 2)
    carbs = round((calories - protein * 4 - fats * 9) / 4, 2)
    return {"calories": calories, "protein": protein, "carbs": carbs, "fats": fats}

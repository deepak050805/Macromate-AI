import pytest

from app.services.nutrition import calculate


@pytest.mark.parametrize("goal,factor", [("fat_loss", 0.9), ("maintain", 1), ("gain", 1.1)])
@pytest.mark.parametrize("weight", [30, 70, 85.37, 350])
def test_formula(weight, goal, factor):
    result = calculate({"weight": weight, "goal": goal})
    assert result["calories"] == round(weight * 33 * factor, 2)
    assert (
        abs(result["calories"] - (4 * result["protein"] + 4 * result["carbs"] + 9 * result["fats"]))
        <= 0.1
    )
    assert all(value > 0 for value in result.values())


@pytest.mark.parametrize(
    "weight", [None, True, False, -1, 0, 29, 351, "NaN", "Infinity", [], {}, "abc"]
)
def test_invalid_weight(weight):
    from app.utils.validation import ValidationError

    with pytest.raises(ValidationError):
        calculate({"weight": weight, "goal": "maintain"})


@pytest.mark.parametrize("goal", [None, "unknown", [], {}])
def test_invalid_goal(goal):
    from app.utils.validation import ValidationError

    with pytest.raises(ValidationError):
        calculate({"weight": 70, "goal": goal})

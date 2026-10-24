import pytest


def test_calculator_page(client):
    response = client.get("/calculator")
    assert response.status_code == 200
    assert 'id="calculator-form"' in response.text
    assert 'min="30"' in response.text
    for key in ("calories", "protein", "carbs", "fats"):
        assert f'id="result-{key}"' in response.text
    assert client.get("/static/js/calculator.js").status_code == 200


@pytest.mark.parametrize("goal,factor", [("maintain", 1), ("fat_loss", 0.9), ("gain", 1.1)])
def test_calculator_api(client, goal, factor):
    response = client.post("/api/macros/calculate", json={"weight": 70, "goal": goal})
    assert response.status_code == 200
    assert response.json["calories"] == round(2310 * factor, 2)


def test_malformed_and_invalid_input(client):
    for body in (
        None,
        [],
        {"weight": "NaN", "goal": "maintain"},
        {"weight": 70, "goal": "unknown"},
    ):
        assert client.post("/api/macros/calculate", json=body).status_code == 400

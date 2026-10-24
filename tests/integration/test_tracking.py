def test_crud(logged_in, account):
    data = {"weight": 72.5, "calories": 2100, "date": "2024-06-01", "email": "ignored@example.test"}
    created = logged_in.post("/api/tracker/add", json=data)
    assert created.status_code == 201
    record_id = created.json["record"]["id"]
    history = logged_in.get("/api/tracker/history").json
    assert history["total"] == 1
    assert history["records"][0]["weight"] == 72.5
    data["weight"] = 73
    assert logged_in.put(f"/api/tracker/{record_id}", json=data).json["record"]["weight"] == 73
    assert logged_in.delete(f"/api/tracker/{record_id}").status_code == 200
    assert logged_in.get("/api/tracker/history").json["total"] == 0
    assert logged_in.delete(f"/api/tracker/{record_id}").status_code == 404


def test_validation(logged_in):
    assert logged_in.post("/api/tracker/add", json={}).status_code == 400
    assert (
        logged_in.post(
            "/api/tracker/add", json={"weight": 70, "calories": 1.5, "date": "2024-06-01"}
        ).status_code
        == 400
    )
    assert logged_in.get("/api/tracker/history?page=0").status_code == 400

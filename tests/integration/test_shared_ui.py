def test_home_and_local_assets(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Skip to content" in response.text
    assert 'href="/calculator"' in response.text
    assert "not AI or machine learning" in response.text
    for asset in ("css/app.css", "js/common.js"):
        assert client.get("/static/" + asset).status_code == 200
    assert "unsafe-inline" not in response.headers["Content-Security-Policy"]

def test_public_startup(client):
    assert client.get("/").status_code == 200
    assert client.get("/health/live").json == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200


def test_factory_does_not_create_schema():
    from app import create_app
    from app.extensions import db
    from sqlalchemy import inspect
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "RATELIMIT_ENABLED": False})
    with app.app_context():
        assert inspect(db.engine).get_table_names() == []

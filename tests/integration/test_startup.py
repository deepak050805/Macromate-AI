import pytest


def test_public_startup(client):
    assert client.get("/").status_code == 200
    assert client.get("/health/live").json == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200


def test_factory_does_not_create_schema():
    from sqlalchemy import inspect

    from app import create_app
    from app.extensions import db

    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "RATELIMIT_ENABLED": False}
    )
    with app.app_context():
        assert inspect(db.engine).get_table_names() == []


def test_factory_production_selection_fails_before_extension_initialization(monkeypatch):
    from app import create_app, db

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setattr("app.load_dotenv", lambda **kwargs: None)

    def unexpected_initialization(app):
        pytest.fail("Invalid production configuration reached database initialization")

    monkeypatch.setattr(db, "init_app", unexpected_initialization)
    with pytest.raises(ValueError, match="Production requires"):
        create_app(
            {
                "APP_ENV": "production",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "SECRET_KEY": None,
            }
        )


def test_factory_testing_selection_can_start_under_a_production_shell(monkeypatch):
    from app import create_app

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr("app.load_dotenv", lambda **kwargs: None)
    app = create_app(
        {
            "APP_ENV": "testing",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SECRET_KEY": "isolated-startup-fixture-key",
            "RATELIMIT_ENABLED": False,
        }
    )
    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert app.test_client().get("/health/live").json == {"status": "ok"}

from flask_migrate import upgrade
from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db


def test_fresh_migration(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "fresh.db"),
            "RATELIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        upgrade()
        assert "otp_challenges" in inspect(db.engine).get_table_names()
        assert (
            db.session.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"
        )


def test_legacy_password_invalidation(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "legacy.db"),
            "RATELIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        upgrade(revision="0001")
        db.session.execute(
            text("INSERT INTO users(email,password) VALUES ('Legacy@Example.test','old-plaintext')")
        )
        db.session.execute(
            text(
                "INSERT INTO progress(email,weight,calories) VALUES ('Legacy@Example.test',70,2000)"
            )
        )
        db.session.commit()
        upgrade()
        row = db.session.execute(text("SELECT email,password FROM users")).first()
        assert tuple(row) == ("legacy@example.test", "!reset-required")
        assert db.session.execute(text("SELECT count(*) FROM progress")).scalar() == 1
        assert db.session.execute(text("SELECT record_date FROM progress")).scalar() is None

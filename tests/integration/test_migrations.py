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
            db.session.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0003"
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

def test_request_identity_migration_preserves_preexisting_progress(tmp_path):
    app = create_app({
        'APP_ENV': 'testing', 'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(tmp_path / 'requests.db'),
        'RATELIMIT_ENABLED': False,
    })
    with app.app_context():
        upgrade(revision='0002')
        db.session.execute(text("INSERT INTO users(email,password,is_verified,role,auth_version) VALUES ('request@example.test','!disabled',1,'user',1)"))
        db.session.execute(text("INSERT INTO progress(email,weight,calories) VALUES ('request@example.test',70,2000)"))
        db.session.commit()
        upgrade()
        assert 'request_key' in {column['name'] for column in inspect(db.engine).get_columns('progress')}
        row = db.session.execute(text('SELECT weight, calories, request_key FROM progress')).one()
        assert tuple(row) == (70, 2000, None)

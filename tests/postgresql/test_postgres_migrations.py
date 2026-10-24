"""Exercise real PostgreSQL DDL and constraints through the migration chain."""

import pytest
from flask_migrate import upgrade
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Progress, User


def test_fresh_migration(postgres_app_factory):
    app = postgres_app_factory()
    with app.app_context():
        upgrade()
        assert set(inspect(db.engine).get_table_names()) == {
            "alembic_version",
            "users",
            "progress",
            "otp_challenges",
        }
        assert (
            db.session.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"
        )
        assert "ix_progress_email_date" in {
            index["name"] for index in inspect(db.engine).get_indexes("progress")
        }


def test_legacy_migration_retains_progress(postgres_app_factory):
    app = postgres_app_factory()
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
        row = db.session.execute(text("SELECT email,password,auth_version FROM users")).one()
        assert tuple(row) == ("legacy@example.test", "!reset-required", 1)
        rows = db.session.execute(
            text("SELECT email,weight,calories,record_date FROM progress")
        ).all()
        assert [tuple(row) for row in rows] == [("legacy@example.test", 70, 2000, None)]


def test_duplicate_normalized_emails_stop_migration(postgres_app_factory, caplog):
    app = postgres_app_factory()
    with app.app_context():
        upgrade(revision="0001")
        db.session.execute(
            text(
                "INSERT INTO users(email,password) VALUES "
                "('Legacy@Example.test','first-password'),"
                "('legacy@example.test','second-password')"
            )
        )
        db.session.commit()
        with pytest.raises(SystemExit) as error:
            upgrade()
        assert error.value.code == 1
        assert "duplicate normalized account emails" in caplog.text
        assert (
            db.session.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0001"
        )
        rows = db.session.execute(text("SELECT email,password FROM users ORDER BY id")).all()
        assert [tuple(row) for row in rows] == [
            ("Legacy@Example.test", "first-password"),
            ("legacy@example.test", "second-password"),
        ]


@pytest.mark.parametrize(
    "fields",
    [
        {"email": "unknown@example.test", "weight": 70, "calories": 2000},
        {"email": "owner@example.test", "weight": 0, "calories": 2000},
        {"email": "owner@example.test", "weight": 70, "calories": -1},
    ],
    ids=["foreign-key", "weight-constraint", "calorie-constraint"],
)
def test_migrated_constraints_reject_invalid_progress(postgres_app_factory, fields):
    app = postgres_app_factory()
    with app.app_context():
        upgrade()
        db.session.add(User(email="owner@example.test", password="!reset-required"))
        db.session.commit()
        db.session.add(Progress(**fields))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.execute(text("SELECT count(*) FROM progress")).scalar() == 0

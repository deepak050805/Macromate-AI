import pytest

from app import create_app
from app.extensions import db
from app.models import User
from app.services.passwords import hash_password


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SECRET_KEY": "test-only-key-not-for-deployment",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def account(app):
    user = User(
        email="person@example.test", password=hash_password("correct horse battery"), is_verified=1
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def logged_in(client, account):
    with client.session_transaction() as session:
        session["user_id"] = account.id
        session["auth_version"] = account.auth_version
    return client

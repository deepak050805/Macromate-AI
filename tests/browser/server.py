"""Loopback-only browser fixture with fictional accounts and in-memory data."""

import os
import sys
from datetime import date
from pathlib import Path


def main():
    os.environ["APP_ENV"] = "testing"
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from werkzeug.serving import make_server

    from app import create_app
    from app.extensions import db
    from app.models import Progress, User
    from app.services.passwords import hash_password

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "browser-fixture-only-key-not-for-deployment",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "RATELIMIT_ENABLED": False,
            "WTF_CSRF_ENABLED": True,
            "OTP_COOLDOWN_SECONDS": 60,
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "",
            "MAIL_DEFAULT_SENDER": "",
            "TRUSTED_HOSTS": ["127.0.0.1"],
        }
    )
    with app.app_context():
        db.create_all()
        password = hash_password("fictional browser password")
        db.session.add_all(
            [
                User(email="browser-owner@example.test", password=password, is_verified=1),
                User(email="browser-pages@example.test", password=password, is_verified=1),
                User(email="browser-settings@example.test", password=password, is_verified=1),
                User(
                    email="browser-admin@example.test",
                    password=password,
                    is_verified=1,
                    role="admin",
                ),
                *[
                    User(email=f"directory-{index}@example.test", password="!disabled-test-fixture")
                    for index in range(26)
                ],
            ]
        )
        db.session.flush()
        db.session.add_all(
            Progress(
                email="browser-pages@example.test",
                weight=70,
                calories=2000,
                record_date=date(2024, 2, day),
            )
            for day in range(1, 22)
        )
        db.session.commit()
    server = make_server("127.0.0.1", 0, app, threaded=True)
    try:
        print(f"BROWSER_TEST_URL=http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()
    finally:
        server.server_close()
        with app.app_context():
            db.session.remove()
            db.engine.dispose()


if __name__ == "__main__":
    main()

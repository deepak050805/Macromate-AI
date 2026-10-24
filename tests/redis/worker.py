"""Run one independent application process; input and output are JSON."""

import json
import sys
from pathlib import Path
from unittest.mock import patch


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from redis.exceptions import ConnectionError

    from app import create_app
    from app.extensions import db

    config = json.load(sys.stdin)
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SECRET_KEY": "redis-test-only-not-for-deployment",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": True,
            "RATELIMIT_STORAGE_URI": config["url"],
            "RATELIMIT_KEY_PREFIX": config["prefix"],
            "RATELIMIT_SWALLOW_ERRORS": False,
            "RATELIMIT_IN_MEMORY_FALLBACK_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        client = app.test_client()

        def login():
            return client.post(
                "/api/auth/login",
                json={"email": "missing@example.test", "password": "test-only-password"},
            )

        if config.get("outage"):
            with patch(
                "redis.client.Redis.execute_command",
                side_effect=ConnectionError("private-rate-limit-driver-diagnostic"),
            ):
                result = login()
                live = client.get("/health/live")
            output = {"status": result.status_code, "body": result.json, "live": live.status_code}
        else:
            results = [login() for _ in range(config["count"])]
            output = {
                "statuses": [result.status_code for result in results],
                "retry_after": results[-1].headers.get("Retry-After"),
            }
        db.session.remove()
        db.engine.dispose()
    print(json.dumps(output))


if __name__ == "__main__":
    main()

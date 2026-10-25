"""Run a real driver against an owned endpoint that never completes its handshake."""

import json
import os
import socketserver
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch


def main():
    os.environ["APP_ENV"] = "testing"
    os.environ.pop("PGCONNECT_TIMEOUT", None)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from app import create_app
    from app.extensions import db

    release = threading.Event()
    connections = []

    class SilentEndpoint(socketserver.BaseRequestHandler):
        def handle(self):
            connections.append(1)
            release.wait(30)

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True
        block_on_close = False

    with Server(("127.0.0.1", 0), SilentEndpoint) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        app = None
        try:
            with patch("app.load_dotenv", return_value=False):
                app = create_app(
                    {
                        "TESTING": True,
                        "SECRET_KEY": "socket-test-only-key-not-for-deployment",
                        "SQLALCHEMY_DATABASE_URI": (
                            "postgresql://fictional:fictional@127.0.0.1:"
                            f"{server.server_address[1]}/fictional"
                        ),
                        "WTF_CSRF_ENABLED": False,
                        "RATELIMIT_ENABLED": False,
                    }
                )
            client = app.test_client()
            kind = sys.argv[1]
            if kind == "html":
                with client.session_transaction() as session:
                    session["user_id"] = 1
                    session["auth_version"] = 0
            started = time.monotonic()
            if kind == "api":
                result = client.post(
                    "/api/auth/login",
                    json={"email": "missing@example.test", "password": "fictional password"},
                )
            elif kind == "html":
                result = client.get("/dashboard")
            else:
                result = client.get("/health/ready")
            elapsed = time.monotonic() - started
            live = client.get("/health/live")
            print(
                json.dumps(
                    {
                        "status": result.status_code,
                        "elapsed": elapsed,
                        "body": result.json if result.is_json else result.get_data(as_text=True),
                        "live": live.status_code,
                        "connections": len(connections),
                        "timeout": app.config["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"][
                            "connect_timeout"
                        ],
                    }
                ),
                flush=True,
            )
        finally:
            release.set()
            server.shutdown()
            thread.join(timeout=2)
            if app is not None:
                with app.app_context():
                    db.session.remove()
                    db.engine.dispose()


if __name__ == "__main__":
    main()

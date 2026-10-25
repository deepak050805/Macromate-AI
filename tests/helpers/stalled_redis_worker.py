"""Exercise real Redis sockets against an owned endpoint that never replies."""

import json
import socketserver
import sys
import threading
import time
from pathlib import Path


def main():
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
        try:
            app = create_app(
                {
                    "TESTING": True,
                    "SECRET_KEY": "socket-test-only-key-not-for-deployment",
                    "SQLALCHEMY_DATABASE_URI": "sqlite://",
                    "WTF_CSRF_ENABLED": False,
                    "RATELIMIT_ENABLED": True,
                    "RATELIMIT_STORAGE_URI": f"redis://127.0.0.1:{server.server_address[1]}/15",
                }
            )
            with app.app_context():
                db.create_all()
            client = app.test_client()
            started = time.monotonic()
            if sys.argv[1] == "api":
                result = client.post(
                    "/api/auth/login",
                    json={"email": "missing@example.test", "password": "fictional password"},
                )
            else:
                result = client.get("/login")
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
                    }
                ),
                flush=True,
            )
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        finally:
            release.set()
            server.shutdown()
            thread.join(timeout=2)


if __name__ == "__main__":
    main()

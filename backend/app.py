"""Compatibility entry point for existing backend.app:app deployments."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()

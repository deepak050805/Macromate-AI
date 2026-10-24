"""Flask factory: no database mutation or external connection on import."""

from dotenv import load_dotenv
from flask import Flask

from app.config import configuration
from app.errors import register_errors
from app.extensions import csrf, db, limiter, migrate
from app.headers import register_headers
from app.logging_config import configure_logging


def create_app(config=None):
    load_dotenv(override=False)
    app = Flask(__name__)
    app.config.update(configuration(config))
    configure_logging(app)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    from app.routes import admin, auth, calculator, health, pages, tracking

    for module in (admin, auth, calculator, health, pages, tracking):
        app.register_blueprint(module.bp)
    from app.security import current_user

    @app.context_processor
    def identity_context():
        return {"viewer": current_user()}

    register_errors(app)
    register_headers(app)
    return app

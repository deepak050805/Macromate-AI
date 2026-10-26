"""Flask factory: no database mutation or external connection on import."""

from dotenv import load_dotenv
from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

from app.commands import register_commands
from app.config import configuration
from app.errors import register_errors
from app.extensions import csrf, db, limiter, migrate
from app.headers import register_headers
from app.logging_config import configure_logging
from app.request_context import register_request_context


def create_app(config=None):
    load_dotenv(override=False)
    app = Flask(__name__)
    app.config.update(configuration(config))
    hops = app.config["TRUSTED_PROXY_HOPS"]
    if hops:
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=hops, x_proto=hops, x_host=0, x_port=0, x_prefix=0
        )
    configure_logging(app)
    register_request_context(app)
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
        viewer = None if request.environ.get("macromate.error_response") else current_user()
        return {"viewer": viewer}

    register_errors(app)
    register_headers(app)
    register_commands(app)
    return app

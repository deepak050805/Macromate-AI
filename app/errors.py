from flask import jsonify, render_template, request
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from app.extensions import db
from app.services.mail import DeliveryError
from app.utils.validation import ValidationError


def register_errors(app):
    def response(message, status, code):
        if request.path.startswith("/api/"):
            return jsonify(message=message, error=code), status
        return render_template("errors/error.html", message=message, status=status), status

    @app.errorhandler(ValidationError)
    def validation(error):
        db.session.rollback()
        return response(str(error), 400, "validation_error")

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return response("Your session expired. Reload the page and try again.", 400, "csrf_error")

    @app.errorhandler(DeliveryError)
    def mail_error(error):
        db.session.rollback()
        return response("Email delivery is temporarily unavailable. Try again later.", 503, "mail_unavailable")

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.error("database_request_failed")
        return response("Service temporarily unavailable", 503, "database_unavailable")

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {401: "Please log in to continue", 403: "Access denied", 404: "Page or record not found", 429: "Too many attempts. Try again later."}
        return response(messages.get(error.code, error.name), error.code, error.name.lower().replace(" ", "_"))

    @app.errorhandler(Exception)
    def unexpected(error):
        db.session.rollback()
        app.logger.error("unexpected_request_failure")
        return response("An unexpected error occurred", 500, "internal_error")

"""Opaque request correlation without trusting client supplied identifiers."""

from uuid import uuid4

from flask import g


def register_request_context(app):
    @app.before_request
    def assign_request_id():
        g.request_id = uuid4().hex

    @app.after_request
    def attach_request_id(response):
        if not getattr(g, "request_id", None):
            g.request_id = uuid4().hex
        response.headers["X-Request-ID"] = g.request_id
        return response

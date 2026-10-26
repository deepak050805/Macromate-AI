import json
import logging
import sys

from flask import g, has_request_context


class EventFormatter(logging.Formatter):
    def format(self, record):
        event = {"level": record.levelname, "logger": record.name, "event": record.getMessage()}
        if has_request_context():
            event["request_id"] = getattr(g, "request_id", None)
        return json.dumps(
            event
        )


def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(EventFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config["LOG_LEVEL"])
    app.logger.propagate = False

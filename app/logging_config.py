import json
import logging
import sys


class EventFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {"level": record.levelname, "logger": record.name, "event": record.getMessage()}
        )


def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(EventFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config["LOG_LEVEL"])
    app.logger.propagate = False

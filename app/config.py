"""Environment configuration; production startup fails closed."""

import os
import secrets
from datetime import timedelta


def configuration(overrides=None):
    env = os.getenv("APP_ENV", "development")
    production = env == "production"
    values = {
        "APP_ENV": env,
        "SECRET_KEY": os.getenv("SECRET_KEY") or (None if production else secrets.token_hex(32)),
        "SQLALCHEMY_DATABASE_URI": os.getenv("DATABASE_URL", ""),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        "SESSION_COOKIE_SECURE": production,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=8),
        "MAX_CONTENT_LENGTH": 16384,
        "WTF_CSRF_TIME_LIMIT": 8 * 60 * 60,
        "RATELIMIT_STORAGE_URI": os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
        "RATELIMIT_HEADERS_ENABLED": True,
        "MAIL_SERVER": os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        "MAIL_PORT": int(os.getenv("MAIL_PORT", "587")),
        "MAIL_USE_TLS": os.getenv("MAIL_USE_TLS", "true").lower() == "true",
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME", ""),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD", ""),
        "MAIL_DEFAULT_SENDER": os.getenv("MAIL_DEFAULT_SENDER", ""),
        "OTP_EXPIRY_SECONDS": int(os.getenv("OTP_EXPIRY_SECONDS", "300")),
        "OTP_COOLDOWN_SECONDS": int(os.getenv("OTP_COOLDOWN_SECONDS", "60")),
        "OTP_MAX_ATTEMPTS": 5,
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "TRUSTED_HOSTS": os.getenv("TRUSTED_HOSTS", "").split(",")
        if os.getenv("TRUSTED_HOSTS")
        else None,
    }
    values.update(overrides or {})
    uri = values["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith("postgres://"):
        values["SQLALCHEMY_DATABASE_URI"] = uri.replace("postgres://", "postgresql://", 1)
    if not uri:
        raise ValueError("DATABASE_URL must be configured")
    if production:
        required = (
            "SECRET_KEY",
            "MAIL_USERNAME",
            "MAIL_PASSWORD",
            "MAIL_DEFAULT_SENDER",
            "TRUSTED_HOSTS",
        )
        if any(not values.get(key) for key in required):
            raise ValueError(
                "Production requires SECRET_KEY, mail credentials, sender and TRUSTED_HOSTS"
            )
        if len(values["SECRET_KEY"]) < 32 or not values["SESSION_COOKIE_SECURE"]:
            raise ValueError("Production requires a strong secret and secure cookies")
        if not values["SQLALCHEMY_DATABASE_URI"].startswith("postgresql://"):
            raise ValueError("Production requires PostgreSQL")
        if not values["RATELIMIT_STORAGE_URI"].startswith(("redis://", "rediss://")):
            raise ValueError("Production requires shared Redis rate-limit storage")
        if not values["MAIL_USE_TLS"]:
            raise ValueError("Production SMTP requires TLS")
    return values

"""Environment configuration; production startup fails closed."""

import logging
import math
import os
import secrets
from collections.abc import Mapping
from datetime import timedelta

from redis.backoff import NoBackoff
from redis.connection import parse_url as parse_redis_url
from redis.retry import Retry
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


def _integer_setting(value, name, minimum, maximum=None):
    bounds = f"between {minimum} and {maximum}" if maximum is not None else f"at least {minimum}"
    message = f"{name} must be an integer {bounds}"
    try:
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise ValueError
        result = int(value)
        if (
            not math.isfinite(result)
            or result < minimum
            or (maximum is not None and result > maximum)
        ):
            raise ValueError
    except (ValueError, OverflowError):
        raise ValueError(message) from None
    return result


def configuration(overrides=None):
    env = (overrides or {}).get("APP_ENV", os.getenv("APP_ENV", "development"))
    if env not in ("development", "testing", "production"):
        raise ValueError("APP_ENV must be development, testing or production")
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
        "MAIL_PORT": os.getenv("MAIL_PORT", "587"),
        "MAIL_USE_TLS": os.getenv("MAIL_USE_TLS", "true"),
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME", ""),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD", ""),
        "MAIL_DEFAULT_SENDER": os.getenv("MAIL_DEFAULT_SENDER", ""),
        "OTP_EXPIRY_SECONDS": os.getenv("OTP_EXPIRY_SECONDS", "300"),
        "OTP_COOLDOWN_SECONDS": os.getenv("OTP_COOLDOWN_SECONDS", "60"),
        "OTP_MAX_ATTEMPTS": 5,
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "TRUSTED_PROXY_HOPS": os.getenv("TRUSTED_PROXY_HOPS", "0"),
        "DATABASE_POOL_TIMEOUT_SECONDS": os.getenv("DATABASE_POOL_TIMEOUT_SECONDS", "5"),
        "TRUSTED_HOSTS": os.getenv("TRUSTED_HOSTS", "").split(",")
        if os.getenv("TRUSTED_HOSTS")
        else None,
    }
    values.update(overrides or {})
    level = values["LOG_LEVEL"]
    if isinstance(level, str):
        level = level.strip()
        names = logging.getLevelNamesMapping()
        if level not in names:
            level = level.upper()
        if level not in names:
            raise ValueError("LOG_LEVEL must be a registered logging name or integer")
    elif isinstance(level, bool) or not isinstance(level, int):
        raise ValueError("LOG_LEVEL must be a registered logging name or integer")
    values["LOG_LEVEL"] = level
    for key in ("MAIL_USE_TLS", "SESSION_COOKIE_SECURE"):
        value = values[key]
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in ("true", "1", "yes", "on"):
                value = True
            elif normalized in ("false", "0", "no", "off"):
                value = False
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be a boolean")
        values[key] = value
    hosts = values["TRUSTED_HOSTS"]
    if hosts is not None:
        if not isinstance(hosts, (list, tuple)) or any(not isinstance(host, str) for host in hosts):
            raise ValueError("TRUSTED_HOSTS must be a list of hostnames")
        values["TRUSTED_HOSTS"] = [host.strip() for host in hosts if host.strip()] or None
    for key, minimum, maximum in (
        ("MAIL_PORT", 1, 65535),
        ("OTP_EXPIRY_SECONDS", 1, None),
        ("OTP_COOLDOWN_SECONDS", 0, None),
        ("OTP_MAX_ATTEMPTS", 1, None),
        ("TRUSTED_PROXY_HOPS", 0, 5),
        ("DATABASE_POOL_TIMEOUT_SECONDS", 1, 300),
    ):
        values[key] = _integer_setting(values[key], key, minimum, maximum)
    storage_uri = values["RATELIMIT_STORAGE_URI"]
    if not isinstance(storage_uri, str) or not storage_uri.strip():
        raise ValueError("RATELIMIT_STORAGE_URI must be a nonblank storage URL")
    if storage_uri.startswith(("redis://", "rediss://")):
        try:
            parse_redis_url(storage_uri)
        except (TypeError, ValueError):
            raise ValueError("RATELIMIT_STORAGE_URI must be a valid Redis URL") from None
        storage_options = values.get("RATELIMIT_STORAGE_OPTIONS")
        if storage_options is not None and not isinstance(storage_options, Mapping):
            raise ValueError("RATELIMIT_STORAGE_OPTIONS must be a mapping")
        values["RATELIMIT_STORAGE_OPTIONS"] = {
            "socket_connect_timeout": 2,
            "socket_timeout": 2,
            "retry": Retry(NoBackoff(), 0),
            **(storage_options or {}),
        }
    uri = values["SQLALCHEMY_DATABASE_URI"]
    if not isinstance(uri, str) or not uri.strip():
        raise ValueError("DATABASE_URL must be a nonblank connection URL")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    if uri.startswith("postgresql://"):
        uri = uri.replace("postgresql://", "postgresql+psycopg2://", 1)
    try:
        database_url = make_url(uri)
    except (ArgumentError, TypeError, ValueError):
        raise ValueError("DATABASE_URL must be a valid connection URL") from None
    values["SQLALCHEMY_DATABASE_URI"] = uri
    if uri.startswith("postgresql+psycopg2://"):
        options = dict(values["SQLALCHEMY_ENGINE_OPTIONS"])
        options.setdefault("pool_timeout", values["DATABASE_POOL_TIMEOUT_SECONDS"])
        connect_args = dict(options.get("connect_args") or {})
        if "connect_timeout" not in database_url.query and "PGCONNECT_TIMEOUT" not in os.environ:
            connect_args.setdefault("connect_timeout", 5)
        options["connect_args"] = connect_args
        values["SQLALCHEMY_ENGINE_OPTIONS"] = options
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
        scalar_credentials = ("SECRET_KEY", "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER")
        if any(not isinstance(values[key], str) or not values[key].strip() for key in scalar_credentials):
            raise ValueError("Production requires nonblank string secrets and mail settings")
        if len(values["SECRET_KEY"]) < 32 or not values["SESSION_COOKIE_SECURE"]:
            raise ValueError("Production requires a strong secret and secure cookies")
        if not values["SQLALCHEMY_DATABASE_URI"].startswith("postgresql+psycopg2://"):
            raise ValueError("Production requires PostgreSQL")
        if not values["RATELIMIT_STORAGE_URI"].startswith(("redis://", "rediss://")):
            raise ValueError("Production requires shared Redis rate-limit storage")
        if not values["MAIL_USE_TLS"]:
            raise ValueError("Production SMTP requires TLS")
    mail_server = values["MAIL_SERVER"]
    if not isinstance(mail_server, str) or (production and not mail_server):
        raise ValueError("MAIL_SERVER must be a nonblank SMTP hostname")
    if mail_server:
        if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in mail_server):
            raise ValueError("MAIL_SERVER must be a valid SMTP hostname")
        try:
            mail_server.encode("idna")
        except UnicodeError:
            raise ValueError("MAIL_SERVER must be a valid SMTP hostname") from None
    sender = values["MAIL_DEFAULT_SENDER"]
    if not isinstance(sender, str):
        raise ValueError("MAIL_DEFAULT_SENDER must be a sender string")
    sender_key = "MAIL_DEFAULT_SENDER" if sender else "MAIL_USERNAME"
    sender = sender or values["MAIL_USERNAME"]
    if not isinstance(sender, str):
        raise ValueError(f"{sender_key} must be a sender string")
    if sender:
        if not sender.strip() or any(ord(character) < 32 or ord(character) == 127 for character in sender):
            raise ValueError(f"{sender_key} must be a valid sender header")
        try:
            sender.encode("utf-8")
        except UnicodeError:
            raise ValueError(f"{sender_key} must be a valid sender header") from None
    return values

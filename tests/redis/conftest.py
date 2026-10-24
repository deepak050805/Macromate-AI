import os
import uuid
from urllib.parse import urlsplit

import pytest
from redis import Redis


@pytest.fixture
def redis_service():
    url = os.environ.get("TEST_REDIS_URL", "")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "redis"
        or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.path != "/15"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        pytest.fail("TEST_REDIS_URL must name a disposable loopback Redis database 15 without auth")
    connection = Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
    prefix = "macromate_test_" + uuid.uuid4().hex
    try:
        connection.ping()
        yield url, prefix
    finally:
        # Never flush a database: delete only this test's unpredictable namespace.
        try:
            for key in connection.scan_iter(match=f"*{prefix}*", count=100):
                connection.delete(key)
        finally:
            connection.close()

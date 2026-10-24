import json
import os
import subprocess
import sys
from pathlib import Path


def worker(url, prefix, count=1, *, outage=False):
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("worker.py"))],
        input=json.dumps({"url": url, "prefix": prefix, "count": count, "outage": outage}),
        env={**os.environ, "APP_ENV": "testing"},
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    assert "private-rate-limit-driver-diagnostic" not in result.stdout + result.stderr
    return json.loads(result.stdout.splitlines()[-1])


def test_limit_is_shared_across_processes(redis_service):
    url, prefix = redis_service
    assert worker(url, prefix, 3)["statuses"] == [401, 401, 401]
    second = worker(url, prefix, 3)
    assert second["statuses"] == [401, 401, 429]
    assert int(second["retry_after"]) > 0


def test_namespaces_are_isolated(redis_service):
    url, prefix = redis_service
    assert worker(url, prefix, 5)["statuses"] == [401] * 5
    assert worker(url, prefix + "_other")["statuses"] == [401]
    assert worker(url, prefix)["statuses"] == [429]


def test_storage_failure_blocks_request_but_not_liveness(redis_service):
    url, prefix = redis_service
    result = worker(url, prefix, outage=True)
    assert result["status"] == 503
    assert result["body"]["error"] == "rate_limit_unavailable"
    assert result["live"] == 200

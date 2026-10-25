import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("kind", ["api", "html"])
def test_unresponsive_storage_fails_closed_without_retries(kind):
    # A subprocess bounds the regression itself if the client's timeout disappears.
    worker = Path(__file__).resolve().parents[1] / "helpers" / "stalled_redis_worker.py"
    result = subprocess.run(
        [sys.executable, str(worker), kind],
        env={**os.environ, "APP_ENV": "testing"},
        capture_output=True,
        text=True,
        check=True,
        timeout=12,
    )
    data = json.loads(result.stdout.splitlines()[-1])
    assert data["status"] == 503
    assert data["elapsed"] < 5
    assert data["connections"] == 1
    assert data["live"] == 200
    if kind == "api":
        assert data["body"]["error"] == "rate_limit_unavailable"
    else:
        assert "Request limiting is temporarily unavailable" in data["body"]

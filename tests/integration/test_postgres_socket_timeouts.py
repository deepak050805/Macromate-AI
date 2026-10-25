import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("kind", ["api", "html", "readiness"])
def test_unresponsive_postgres_handshake_returns_safe_503(kind):
    worker = Path(__file__).resolve().parents[1] / "helpers" / "stalled_postgres_worker.py"
    result = subprocess.run(
        [sys.executable, str(worker), kind],
        env={**os.environ, "APP_ENV": "testing"},
        capture_output=True,
        text=True,
        check=True,
        timeout=45,
    )
    data = json.loads(result.stdout.splitlines()[-1])
    assert data["timeout"] == 5
    assert data["status"] == 503
    assert data["elapsed"] < 8
    assert data["connections"] == 1
    assert data["live"] == 200
    assert "fictional" not in str(data["body"])
    if kind == "api":
        assert data["body"]["error"] == "database_unavailable"
    elif kind == "html":
        assert "Service temporarily unavailable" in data["body"]
    else:
        assert data["body"] == {"status": "unavailable"}

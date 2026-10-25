"""Bounded loopback liveness probe; never use configured outbound HTTP proxies."""

import json
from http.client import HTTPException
from urllib.request import ProxyHandler, build_opener


def main():
    try:
        opener = build_opener(ProxyHandler({}))
        with opener.open("http://127.0.0.1:8000/health/live", timeout=2) as response:
            data = json.loads(response.read(1024))
            healthy = (
                response.status == 200 and isinstance(data, dict) and data.get("status") == "ok"
            )
            return 0 if healthy else 1
    except (OSError, ValueError, HTTPException):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

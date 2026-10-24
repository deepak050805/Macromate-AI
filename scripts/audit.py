"""Audit resolved Python requirements and the frontend lockfile; network required."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPM = "npm.cmd" if os.name == "nt" else "npm"


def main():
    checks = [
        [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            "requirements-dev.txt",
            "--progress-spinner",
            "off",
        ],
        [NPM, "run", "audit:check"],
    ]
    for command in checks:
        print("Running:", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()

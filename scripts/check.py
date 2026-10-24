"""Run the local quality gate without activating a shell environment."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPM = "npm.cmd" if os.name == "nt" else "npm"


def main():
    checks = [
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        [sys.executable, "-m", "pytest"],
        [NPM, "run", "test:frontend"],
        [NPM, "run", "lint"],
        [NPM, "run", "format:check"],
    ]
    for command in checks:
        print("Running:", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()

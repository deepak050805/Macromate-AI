"""Build and verify a disposable runtime image without touching existing services."""

import json
import subprocess
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
OPENER = build_opener(ProxyHandler({}))


def run(*args, capture=True, check=True, timeout=60):
    return subprocess.run(
        args, cwd=ROOT, text=True, capture_output=capture, check=check, timeout=timeout
    )


def output(*args):
    return run(*args).stdout.strip()


def owned_container(container, name, token):
    info = json.loads(output("docker", "inspect", container))[0]
    if info["Name"] != "/" + name or info["Config"]["Labels"].get("macromate.check") != token:
        raise RuntimeError("Refusing to control a container with an unexpected identity")
    return info


def response(url):
    try:
        result = OPENER.open(url, timeout=2)
    except HTTPError as error:
        result = error
    with result:
        return result.status, result.read()


def main():
    token = uuid.uuid4().hex
    image = "macromate-check:" + token
    name = "macromate-check-" + token
    containers = []
    image_id = None

    def create(suffix, *args):
        container_name = name + "-" + suffix
        container_id = output(
            "docker",
            "create",
            "--name",
            container_name,
            "--label",
            f"macromate.check={token}",
            *args,
        )
        containers.append((container_id, container_name))
        return container_id, container_name

    try:
        run("docker", "build", "--tag", image, ".", capture=False, timeout=600)
        image_id = output("docker", "image", "inspect", image, "--format", "{{.Id}}")
        if (
            output("docker", "image", "inspect", image, "--format", "{{.Config.User}}")
            != "10001:10001"
        ):
            raise RuntimeError("Runtime image must declare the non-root application user")

        # The health probe must fail without a server and startup must require config.
        probe_id, probe_name = create(
            "probe", "--entrypoint", "python", image, "/app/scripts/container_health.py"
        )
        probe = run("docker", "start", "--attach", probe_id, check=False, timeout=15)
        if (
            owned_container(probe_id, probe_name, token)["State"]["ExitCode"] != 1
            or probe.stdout
            or probe.stderr
        ):
            raise RuntimeError("Unavailable liveness must fail quietly")
        config_id, config_name = create("unconfigured", image)
        run("docker", "start", "--attach", config_id, check=False, timeout=30)
        if owned_container(config_id, config_name, token)["State"]["ExitCode"] == 0:
            raise RuntimeError("Unconfigured production startup must fail closed")

        container, container_name = create(
            "web",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--publish",
            "127.0.0.1::8000",
            "--env",
            "APP_ENV=testing",
            "--env",
            "DATABASE_URL=sqlite://",
            "--env",
            "RATELIMIT_STORAGE_URI=memory://",
            "--env",
            "SECRET_KEY=container-test-only-key-not-for-deployment",
            image,
        )
        run("docker", "start", container)
        info = owned_container(container, container_name, token)
        bindings = info["NetworkSettings"]["Ports"]["8000/tcp"]
        if len(bindings) != 1 or bindings[0]["HostIp"] != "127.0.0.1":
            raise RuntimeError("Test HTTP service must bind only to loopback")
        base = "http://127.0.0.1:" + bindings[0]["HostPort"]
        deadline = time.monotonic() + 60
        while True:
            try:
                status, body = response(base + "/health/live")
                if status == 200 and json.loads(body) == {"status": "ok"}:
                    break
            except (URLError, OSError, ValueError):
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError("Gunicorn did not become live")
            time.sleep(0.5)

        if response(base + "/")[0] != 200 or response(base + "/static/js/common.js")[0] != 200:
            raise RuntimeError("Image must include application templates and static assets")
        if response(base + "/health/ready")[0] != 503:
            raise RuntimeError("Startup must leave an empty database schema unready")
        run("docker", "exec", container, "python", "-m", "pip", "check")
        run(
            "docker",
            "exec",
            container,
            "python",
            "-c",
            "import os, importlib.util; from pathlib import Path; "
            "assert os.getuid() == 10001; "
            "assert b'gunicorn' in Path('/proc/1/cmdline').read_bytes(); "
            "assert all(not Path('/app', p).exists() for p in "
            "['.env', '.git', '.venv', 'node_modules', 'tests', '.task-work']); "
            "assert all(importlib.util.find_spec(p) is None for p in ['pytest', 'ruff']); "
            "Path('/tmp/runtime-check').write_text('temporary')",
        )
        run(
            "docker",
            "exec",
            "--env",
            "HTTP_PROXY=http://127.0.0.1:1",
            "--env",
            "http_proxy=http://127.0.0.1:1",
            "--env",
            "NO_PROXY=",
            "--env",
            "no_proxy=",
            container,
            "python",
            "/app/scripts/container_health.py",
        )
        deadline = time.monotonic() + 45
        while (
            owned_container(container, container_name, token)["State"]["Health"]["Status"]
            != "healthy"
        ):
            if time.monotonic() >= deadline:
                raise RuntimeError("Docker liveness health check did not become healthy")
            time.sleep(1)
        run("docker", "stop", "--time", "10", container, timeout=30)
        if owned_container(container, container_name, token)["State"]["ExitCode"] != 0:
            raise RuntimeError("Gunicorn did not exit gracefully on SIGTERM")
        print("Container checks passed: non-root, read-only runtime, pages/assets, liveness,")
        print("empty-schema readiness, fail-closed config, proxy-independent probe and SIGTERM.")
    finally:
        for container_id, container_name in reversed(containers):
            owned_container(container_id, container_name, token)
            run("docker", "rm", "--force", container_id)
        if image_id:
            if output("docker", "image", "inspect", image, "--format", "{{.Id}}") != image_id:
                raise RuntimeError("Refusing to remove an image tag with an unexpected identity")
            run("docker", "image", "rm", image)
        print("Removed only the check's own container and unique image tag.")


if __name__ == "__main__":
    main()

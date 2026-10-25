"""Verify local development services with disposable credentials and owned volumes."""

import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

import psycopg2
import redis

ROOT = Path(__file__).resolve().parents[1]
SERVICES = {"postgres": (5432, "/var/lib/postgresql/data"), "redis": (6379, "/data")}


def isolated_environment(source):
    """Do not let shell interpolation override the check's explicit env file."""
    return {
        key: value
        for key, value in source.items()
        if not key.upper().startswith(("COMPOSE_", "POSTGRES_", "REDIS_"))
    }


def require_local_endpoint(endpoint):
    if not endpoint.startswith(("unix:///", "npipe:////./pipe/")):
        raise RuntimeError("This disposable service check requires a local Docker socket")


def validate_model(model, project):
    """Reject shared storage or non-loopback ports before creating any resources."""
    if model.get("name") != project or set(model.get("services", {})) != set(SERVICES):
        raise RuntimeError("Unexpected Compose project or services")
    expected_volumes = {service + "-data" for service in SERVICES}
    if set(model.get("volumes", {})) != expected_volumes:
        raise RuntimeError("Unexpected Compose volumes")
    for name, volume in model["volumes"].items():
        if volume.get("external") or volume.get("name") != f"{project}_{name}":
            raise RuntimeError("Refusing shared or external volumes")
    if set(model.get("networks", {})) != {"default"}:
        raise RuntimeError("Unexpected Compose networks")
    network = model["networks"]["default"]
    if network.get("external") or network.get("name") != project + "_default":
        raise RuntimeError("Refusing shared or external networks")
    for service, (port, destination) in SERVICES.items():
        config = model["services"][service]
        if config.get("container_name") or config.get("network_mode"):
            raise RuntimeError("Refusing shared container identities or host networking")
        ports = config.get("ports", [])
        if len(ports) != 1 or (
            ports[0].get("host_ip"),
            ports[0].get("target"),
            ports[0].get("published"),
        ) != ("127.0.0.1", port, "0"):
            raise RuntimeError("Check services must publish dynamic loopback ports only")
        mounts = config.get("volumes", [])
        if len(mounts) != 1 or (
            mounts[0].get("type"),
            mounts[0].get("source"),
            mounts[0].get("target"),
        ) != ("volume", service + "-data", destination):
            raise RuntimeError("Refusing bind mounts or unexpected service storage")


def validate_identity(info, kind, project):
    labels = info.get("Labels") if kind != "container" else info["Config"].get("Labels")
    labels = labels or {}
    if labels.get("com.docker.compose.project") != project:
        raise RuntimeError("Refusing a resource with an unexpected project owner")
    if kind == "container":
        service = labels.get("com.docker.compose.service")
        if service not in SERVICES or info["Name"] != f"/{project}-{service}-1":
            raise RuntimeError("Refusing an unexpected container identity")
        mounts = info.get("Mounts", [])
        if len(mounts) != 1 or (
            mounts[0].get("Type"),
            mounts[0].get("Name"),
            mounts[0].get("Destination"),
        ) != ("volume", f"{project}_{service}-data", SERVICES[service][1]):
            raise RuntimeError("Refusing a container with unexpected storage")
    else:
        resource = labels.get("com.docker.compose." + kind)
        allowed = {service + "-data" for service in SERVICES} if kind == "volume" else {"default"}
        if resource not in allowed or info["Name"] != f"{project}_{resource}":
            raise RuntimeError("Refusing an unexpected storage/network identity")


class ServiceCheck:
    def __init__(self, env_file, project, environment):
        self.project = project
        self.environment = environment
        self.command = [
            "docker",
            "compose",
            "--env-file",
            str(env_file),
            "--project-name",
            project,
            "--file",
            str(ROOT / "compose.yaml"),
        ]

    def run(self, *args, timeout=120):
        return subprocess.run(
            args,
            cwd=ROOT,
            env=self.environment,
            text=True,
            capture_output=True,
            check=True,
            timeout=timeout,
        ).stdout.strip()

    def compose(self, *args):
        return self.run(*self.command, *args, timeout=240)

    def resources(self):
        owned = {}
        for kind in ("container", "volume", "network"):
            # Include name matches, not just labels: a name collision must fail closed.
            listing = ("ps", "--all", "--quiet") if kind == "container" else (kind, "ls", "--quiet")
            identifiers = self.run(
                "docker", *listing, "--filter", "name=" + self.project
            ).splitlines()
            for identifier in identifiers:
                prefix = [] if kind == "container" else [kind]
                info = json.loads(self.run("docker", *prefix, "inspect", identifier))[0]
                validate_identity(info, kind, self.project)
                if kind == "container":
                    owned[info["Config"]["Labels"]["com.docker.compose.service"]] = info
        return owned

    def up(self):
        self.compose("up", "--detach", "--wait", "--wait-timeout", "90")
        containers = self.resources()
        if set(containers) != set(SERVICES):
            raise RuntimeError("Both service containers must be running")
        ports = {}
        for service, info in containers.items():
            if info["State"].get("Health", {}).get("Status") != "healthy":
                raise RuntimeError("Service did not become healthy")
            bindings = info["NetworkSettings"]["Ports"][f"{SERVICES[service][0]}/tcp"]
            if len(bindings) != 1 or bindings[0]["HostIp"] != "127.0.0.1":
                raise RuntimeError("Service must bind only to loopback")
            ports[service] = int(bindings[0]["HostPort"])
        return ports

    def down(self, *, volumes=False):
        self.resources()  # Validate actual identities and mounts before any removal.
        self.compose("down", "--timeout", "30", *(["--volumes"] if volumes else []))
        if self.resources():
            raise RuntimeError("Service containers remain after teardown")
        if volumes:
            for kind in ("volume", "network"):
                if self.run("docker", kind, "ls", "--quiet", "--filter", "name=" + self.project):
                    raise RuntimeError("Owned storage/network remains after final cleanup")


def postgres_connection(port, password):
    return psycopg2.connect(
        host="127.0.0.1",
        hostaddr="127.0.0.1",
        port=port,
        user="macromate_check",
        dbname="macromate_check",
        password=password,
        connect_timeout=3,
        sslmode="disable",
        options="",
    )


def verify_required_passwords(directory, project, environment):
    """Exercise Compose's required-variable errors without loading a personal env file."""
    path = Path(directory) / "missing-password.env"
    for key in ("POSTGRES_PASSWORD", "REDIS_PASSWORD"):
        other = "REDIS_PASSWORD" if key == "POSTGRES_PASSWORD" else "POSTGRES_PASSWORD"
        for value in (None, ""):
            path.write_text(
                f"{other}=disposable\n" + ("" if value is None else f"{key}=\n"),
                encoding="utf-8",
            )
            try:
                ServiceCheck(path, project, environment).compose("config", "--quiet")
            except subprocess.CalledProcessError as error:
                if key not in error.stderr:
                    raise RuntimeError("Expected a named missing-password error") from error
            else:
                raise RuntimeError("Compose accepted a missing/empty service password")


def verify_services(ports, password, marker, *, first):
    try:
        connection = postgres_connection(ports["postgres"], "incorrect-" + password)
    except psycopg2.OperationalError as error:
        if "password authentication failed" not in str(error):
            raise RuntimeError("Expected PostgreSQL password rejection") from error
    else:
        connection.close()
        raise RuntimeError("PostgreSQL accepted an incorrect password")
    connection = postgres_connection(ports["postgres"], password)
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            if first:
                cursor.execute("CREATE TABLE compose_probe (value TEXT NOT NULL)")
                cursor.execute("INSERT INTO compose_probe VALUES (%s)", (marker,))
            cursor.execute("SELECT value FROM compose_probe")
            if cursor.fetchall() != [(marker,)]:
                raise RuntimeError("PostgreSQL did not preserve its committed marker")
    finally:
        connection.close()

    for invalid in (None, "incorrect-" + password):
        with redis.Redis(
            host="127.0.0.1",
            port=ports["redis"],
            password=invalid,
            socket_timeout=3,
            socket_connect_timeout=3,
        ) as client:
            try:
                client.ping()
            except redis.AuthenticationError:
                pass
            else:
                raise RuntimeError("Redis accepted a missing/incorrect password")
    with redis.Redis(
        host="127.0.0.1",
        port=ports["redis"],
        password=password,
        socket_timeout=3,
        socket_connect_timeout=3,
        decode_responses=True,
    ) as client:
        if first:
            client.set("compose-probe", marker)
        if client.get("compose-probe") != marker:
            raise RuntimeError("Redis did not preserve its marker")


def main():
    project = "macromate-services-check-" + uuid.uuid4().hex
    environment = isolated_environment(os.environ)
    # Credentials deliberately exercise literal spaces, dollar signs and URL punctuation.
    password = "disposable $ @:" + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix=project + "-") as directory:
        env_file = Path(directory) / "services.env"
        env_file.write_text(
            "POSTGRES_USER=macromate_check\nPOSTGRES_DB=macromate_check\n"
            f"POSTGRES_PASSWORD='{password}'\nREDIS_PASSWORD='{password}'\n"
            "POSTGRES_PORT=0\nREDIS_PORT=0\n",
            encoding="utf-8",
        )
        check = ServiceCheck(env_file, project, environment)
        if environment.get("DOCKER_CONTEXT") or not environment.get("DOCKER_HOST"):
            context = environment.get("DOCKER_CONTEXT")
            endpoint = json.loads(
                check.run(
                    "docker",
                    "context",
                    "inspect",
                    *([context] if context else []),
                    "--format",
                    "{{json .Endpoints.docker.Host}}",
                )
            )
        else:
            endpoint = environment["DOCKER_HOST"]
        require_local_endpoint(endpoint)
        verify_required_passwords(directory, project, environment)
        model = json.loads(check.compose("config", "--format", "json"))
        validate_model(model, project)
        if check.resources():
            raise RuntimeError("Disposable project already has containers")
        print("Checking isolated PostgreSQL/Redis services: " + project, flush=True)
        try:
            ports = check.up()
            verify_services(ports, password, project, first=True)
            print("Both services are healthy; authenticated markers written.", flush=True)
            check.down()  # Normal operator teardown must preserve the named volumes.
            ports = check.up()
            verify_services(ports, password, project, first=False)
            print(
                "Passed: loopback ports, health, authentication and recreated-container persistence."
            )
        finally:
            check.down(volumes=True)  # Only this UUID project's validated test storage.
            print("Removed only the check's own containers, network and disposable volumes.")


if __name__ == "__main__":
    main()

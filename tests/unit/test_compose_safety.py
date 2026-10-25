"""Offline guards for a checker that creates and deletes disposable Docker storage."""

from copy import deepcopy
from pathlib import Path

import pytest

from scripts.check_compose import (
    SERVICES,
    ServiceCheck,
    isolated_environment,
    require_local_endpoint,
    validate_identity,
    validate_model,
)

PROJECT = "macromate-services-check-test"


@pytest.fixture
def model():
    return {
        "name": PROJECT,
        "services": {
            service: {
                "ports": [{"host_ip": "127.0.0.1", "target": port, "published": "0"}],
                "volumes": [{"type": "volume", "source": service + "-data", "target": target}],
            }
            for service, (port, target) in SERVICES.items()
        },
        "volumes": {
            service + "-data": {"name": f"{PROJECT}_{service}-data"} for service in SERVICES
        },
        "networks": {"default": {"name": PROJECT + "_default"}},
    }


def test_safe_model_is_accepted_without_modification(model):
    before = deepcopy(model)
    validate_model(model, PROJECT)
    assert model == before


@pytest.mark.parametrize("service", SERVICES)
@pytest.mark.parametrize("binding", ["0.0.0.0", "::", "192.168.1.1", ""])
def test_public_and_unspecified_bindings_are_refused(model, service, binding):
    model["services"][service]["ports"][0]["host_ip"] = binding
    with pytest.raises(RuntimeError, match="loopback"):
        validate_model(model, PROJECT)


@pytest.mark.parametrize("service", SERVICES)
def test_existing_bind_storage_is_refused(model, service):
    model["services"][service]["volumes"][0].update(type="bind", source="/existing/data")
    with pytest.raises(RuntimeError, match="bind mounts"):
        validate_model(model, PROJECT)


@pytest.mark.parametrize("kind,key", [("volumes", "postgres-data"), ("networks", "default")])
@pytest.mark.parametrize("change", [{"external": True}, {"name": "existing-shared-resource"}])
def test_external_or_shared_storage_and_networks_are_refused(model, kind, key, change):
    model[kind][key].update(change)
    with pytest.raises(RuntimeError, match="shared or external"):
        validate_model(model, PROJECT)


@pytest.mark.parametrize("change", [{"container_name": "existing-db"}, {"network_mode": "host"}])
def test_shared_container_identity_or_host_networking_is_refused(model, change):
    model["services"]["postgres"].update(change)
    with pytest.raises(RuntimeError, match="shared container"):
        validate_model(model, PROJECT)


@pytest.mark.parametrize(
    "endpoint",
    ["tcp://127.0.0.1:2375", "ssh://host", "tcp://remote:2376", "npipe:////remote/pipe/docker", ""],
)
def test_remote_or_ambiguous_docker_endpoints_are_refused(endpoint):
    with pytest.raises(RuntimeError, match="local Docker socket"):
        require_local_endpoint(endpoint)


@pytest.mark.parametrize(
    "endpoint", ["unix:///var/run/docker.sock", "npipe:////./pipe/docker_engine"]
)
def test_local_docker_sockets_are_accepted(endpoint):
    require_local_endpoint(endpoint)


def test_shell_credentials_and_compose_overrides_cannot_replace_disposable_config():
    original = {
        "POSTGRES_PASSWORD": "personal",
        "REDIS_PASSWORD": "personal",
        "COMPOSE_FILE": "/existing/compose.yaml",
        "COMPOSE_PROJECT_NAME": "existing",
        "COMPOSE_ENV_FILES": "/existing/secrets.env",
        "postgres_port": "5432",
        "PATH": "/tools",
        "DOCKER_CONTEXT": "selected-context",
    }
    assert isolated_environment(original) == {
        "PATH": "/tools",
        "DOCKER_CONTEXT": "selected-context",
    }
    assert original["POSTGRES_PASSWORD"] == "personal"


@pytest.fixture
def container():
    return {
        "Name": f"/{PROJECT}-postgres-1",
        "Config": {
            "Labels": {
                "com.docker.compose.project": PROJECT,
                "com.docker.compose.service": "postgres",
            }
        },
        "Mounts": [
            {
                "Type": "volume",
                "Name": PROJECT + "_postgres-data",
                "Destination": "/var/lib/postgresql/data",
            }
        ],
    }


def test_owned_container_is_accepted(container):
    validate_identity(container, "container", PROJECT)


@pytest.mark.parametrize("field", ["owner", "name", "storage"])
def test_container_identity_and_storage_mismatches_block_cleanup(container, field):
    if field == "owner":
        container["Config"]["Labels"]["com.docker.compose.project"] = "existing"
    elif field == "name":
        container["Name"] = "/existing-db"
    else:
        container["Mounts"][0]["Name"] = "existing-data"
    with pytest.raises(RuntimeError, match="Refusing"):
        validate_identity(container, "container", PROJECT)


@pytest.mark.parametrize("kind,resource", [("volume", "postgres-data"), ("network", "default")])
def test_cleanup_requires_both_resource_name_and_owner_labels(kind, resource):
    info = {
        "Name": f"{PROJECT}_{resource}",
        "Labels": {"com.docker.compose.project": PROJECT, "com.docker.compose." + kind: resource},
    }
    validate_identity(info, kind, PROJECT)
    info["Labels"]["com.docker.compose.project"] = "existing"
    with pytest.raises(RuntimeError, match="project owner"):
        validate_identity(info, kind, PROJECT)


def test_cleanup_does_not_issue_destructive_commands_after_failed_ownership(monkeypatch):
    check = ServiceCheck(Path("unused-test-config.env"), PROJECT, {})
    commands = []

    def refuse():
        raise RuntimeError("foreign resource")

    monkeypatch.setattr(check, "resources", refuse)
    monkeypatch.setattr(check, "compose", lambda *args: commands.append(args))
    with pytest.raises(RuntimeError, match="foreign resource"):
        check.down(volumes=True)
    assert commands == []

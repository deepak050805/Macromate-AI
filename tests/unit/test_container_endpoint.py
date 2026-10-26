import json

import pytest

from scripts import check_container
from scripts.docker_endpoint import require_local_docker


@pytest.mark.parametrize("endpoint", [
    "unix:///var/run/docker.sock", "npipe:////./pipe/dockerDesktopLinuxEngine",
])
def test_explicit_local_host_does_not_inspect_an_unselected_context(endpoint):
    def unexpected(*args):
        pytest.fail("An explicit host must take precedence over the default context")

    assert require_local_docker({"DOCKER_HOST": endpoint}, unexpected) == endpoint


@pytest.mark.parametrize("context", [None, "desktop-linux"])
def test_selected_context_endpoint_is_inspected(context):
    environment = {"DOCKER_CONTEXT": context} if context else {}
    calls = []

    def output(*args):
        calls.append(args)
        return json.dumps("unix:///var/run/docker.sock")

    assert require_local_docker(environment, output) == "unix:///var/run/docker.sock"
    assert calls == [(
        "docker", "context", "inspect", *([context] if context else []),
        "--format", "{{json .Endpoints.docker.Host}}",
    )]


def test_explicit_context_takes_precedence_over_a_remote_host():
    def output(*args):
        assert args[3] == "desktop-linux"
        return json.dumps("npipe:////./pipe/dockerDesktopLinuxEngine")

    endpoint = require_local_docker({
        "DOCKER_CONTEXT": "desktop-linux", "DOCKER_HOST": "ssh://remote.invalid",
    }, output)
    assert endpoint == "npipe:////./pipe/dockerDesktopLinuxEngine"


@pytest.mark.parametrize("endpoint", [
    "tcp://127.0.0.1:2375", "tcp://remote.invalid:2376", "ssh://remote.invalid",
    "http://remote.invalid", "npipe:////remote/pipe/docker_engine",
])
@pytest.mark.parametrize("use_context", [False, True])
def test_remote_or_unproven_daemons_are_rejected(endpoint, use_context):
    environment = {"DOCKER_CONTEXT": "remote"} if use_context else {"DOCKER_HOST": endpoint}

    def output(*args):
        assert use_context
        return json.dumps(endpoint)

    with pytest.raises(RuntimeError, match="requires a local Docker socket"):
        require_local_docker(environment, output)


@pytest.mark.parametrize("raw", ["not-json", "null", "42", "{}"])
def test_invalid_context_results_fail_closed(raw):
    with pytest.raises(RuntimeError):
        require_local_docker({}, lambda *args: raw)


def test_container_check_refuses_a_remote_daemon_before_any_mutation(monkeypatch):
    monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
    monkeypatch.setenv("DOCKER_HOST", "ssh://remote.invalid")

    def forbidden(*args, **kwargs):
        pytest.fail("No Docker operation may run after selecting a remote daemon")

    monkeypatch.setattr(check_container, "run", forbidden)
    monkeypatch.setattr(check_container, "output", forbidden)
    with pytest.raises(RuntimeError, match="requires a local Docker socket"):
        check_container.main()

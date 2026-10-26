"""Resolve Docker context precedence before disposable local service mutations."""

import json


def require_local_docker(environment, output):
    """Use the same daemon selection as Docker; reject remote sockets before work."""
    context = environment.get("DOCKER_CONTEXT")
    if context or not environment.get("DOCKER_HOST"):
        raw = output(
            "docker", "context", "inspect", *([context] if context else []),
            "--format", "{{json .Endpoints.docker.Host}}",
        )
        try:
            endpoint = json.loads(raw)
        except (TypeError, ValueError):
            raise RuntimeError("Unable to resolve the selected Docker endpoint") from None
    else:
        endpoint = environment["DOCKER_HOST"]
    if not isinstance(endpoint, str) or not endpoint.startswith(("unix:///", "npipe:////./pipe/")):
        raise RuntimeError("This disposable service check requires a local Docker socket")
    return endpoint

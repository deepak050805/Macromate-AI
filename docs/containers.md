# Container runtime

The Dockerfile packages the existing Flask factory with runtime dependencies and
Gunicorn on port 8000. It uses a digest-pinned Python 3.12 base and UID/GID 10001.
An allowlist build context excludes local environment files, Git history, virtual
environments and development artifacts. Application files remain owned by root.

Build and run the automated disposable check from a machine with Docker:

```powershell
.\.venv\Scripts\python scripts/check_container.py
```

The check builds a unique image and verifies non-root execution, runtime dependency
compatibility, pages/static assets, a read-only root filesystem, temporary storage,
empty-schema readiness, missing-config refusal, liveness and graceful SIGTERM.
Its temporary containers are labeled and their identities verified before cleanup;
only those containers and its unique image tag are removed. CI runs this separately
from application tests. No database, Redis or mail provider is contacted by this
smoke test.

For a calculator-only local demonstration:

```powershell
docker build --tag macromate:local .
docker run --rm --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --publish 127.0.0.1:8000:8000 --env APP_ENV=testing --env DATABASE_URL=sqlite:// --env RATELIMIT_STORAGE_URI=memory:// --env SECRET_KEY=local-demo-only-key-not-for-deployment macromate:local
```

Open `http://127.0.0.1:8000`. This explicitly selects an ephemeral test configuration:
accounts and persistence are unavailable, and readiness correctly returns 503.

## Deployment configuration

The image defaults to `APP_ENV=production` and refuses to start without the
application's required configuration. Supply runtime secrets through your deployment
environment; never bake `.env` or credentials into an image. PostgreSQL and Redis
URLs must resolve from inside the container. A container's `localhost` is not the
host database. Mail settings, trusted hosts, strong secrets and external HTTPS
ingress still need configuration. See the [README](../README.md#configuration-and-deployment).

Keep `127.0.0.1` in `TRUSTED_HOSTS` for the internal health probe. The probe requests
only `/health/live`, bypasses outbound HTTP proxies, has a two-second timeout and
returns failure quietly. It does not establish database, Redis or SMTP readiness.
Use `/health/ready` separately for the documented schema-readiness contract.

Startup never runs migrations. Follow the [migration guide](migrations.md), take
and verify backups, then execute the approved migration as a separate one-off
command using the same image and runtime configuration:

```sh
docker run --rm --env-file runtime.env macromate:local flask --app app:create_app db upgrade
```

`runtime.env` must be an untracked, separately supplied production configuration;
the demonstration settings above are unsuitable. No migration or deployment is
performed by building the image or running the smoke check. Override the container
command when tuning Gunicorn workers and trusted proxy settings for your ingress.

## Maintenance and limits

Runtime packages follow the existing `requirements.txt` ranges, so builds are not
guaranteed to be byte-identical. Update the base digest deliberately, rebuild, and
rerun tests and dependency audits. The lifecycle smoke test is not an operating
system vulnerability scan, load test, provider-delivery check or production rollout.
Local PostgreSQL/Redis composition is a separate roadmap item.

References: [Docker Python guide](https://docs.docker.com/guides/python/) and
[Gunicorn 23 settings](https://docs.gunicorn.org/en/23.0.0/settings.html).

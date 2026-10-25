# Redis integration testing

The default quality gate uses isolated SQLite databases. Most tests disable rate
limiting; two socket-stall cases enable the real Redis driver against an owned
loopback TCP endpoint that never replies. Run the explicit service suite below
against a **disposable local Redis 8 service**, never an
existing application cache. CI supplies a fresh service without production secrets.

```powershell
docker run --detach --rm --name macromate-redis-test --publish 127.0.0.1:6379:6379 redis:8
$env:APP_ENV = "testing"
$env:TEST_REDIS_URL = "redis://127.0.0.1:6379/15"
.\.venv\Scripts\python -m pytest tests/redis
docker stop macromate-redis-test
```

The fixture requires an explicit unauthenticated loopback `redis://` URL naming
database 15, without query parameters. Missing configuration or a failed connection
fails the suite rather than silently skipping it. Each test uses a random namespace;
cleanup deletes only keys containing that namespace and never flushes the database.

Tests launch separate Python application processes with the same namespace to
verify that login attempts share the five-per-minute limit. A second namespace
verifies isolation. Each process uses an empty in-memory SQLite database and
fictional login credentials; email delivery and production records are untouched.

The outage case injects a Redis connection error into the actual limiter request
path. It verifies a generic HTTP 503, no driver diagnostic in output, and working
liveness. The request fails closed: no in-memory fallback or swallowed storage
errors are enabled. Default regression cases also cover wrapped storage exceptions
and HTML responses. This is not a real network partition, failover, load test,
Redis Cluster test, or validation of deployment timeouts.

## Request-path timeout defaults

For `redis://` and `rediss://`, storage now defaults to a two-second socket
connection timeout, a two-second socket read timeout, and zero automatic retries.
A stalled socket returns the existing generic HTTP 503 rather than occupying a
worker indefinitely. Limits still fail closed; no fallback or swallowed errors
are enabled. The supported client is declared directly as `redis>=7.4.1,<8`.

Explicit `RATELIMIT_STORAGE_OPTIONS` passed to the factory can override individual
defaults without mutating the caller's dictionary. Redis URL query options take
precedence for their driver fields. Non-Redis storage receives no Redis defaults.
Revalidate the request budget if configuring different options.

`tests/integration/test_redis_socket_timeouts.py` checks real socket stalls on API
and HTML routes, a single client connection, safe 503 responses and working
liveness. Each child owns its loopback listener and in-memory database. Its request
latency assertion excludes interpreter startup; a separate process watchdog bounds
the regression itself. No existing Redis server is paused or reconfigured.

Socket timeouts apply to I/O phases, not a universal HTTP deadline. DNS resolution,
multiple successful operations, scheduler delays, cluster failover and deployment
network policy are outside this test's guarantees. See the
[redis-py retry reference](https://redis.readthedocs.io/en/stable/retry.html).

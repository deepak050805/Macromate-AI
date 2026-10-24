# Redis integration testing

The default quality gate uses isolated SQLite databases and disables rate limiting.
Run this explicit suite against a **disposable local Redis 8 service**, never an
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

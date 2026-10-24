# PostgreSQL integration tests

The default `python -m pytest` command runs the unit, integration and security
directories using isolated SQLite databases. The PostgreSQL suite is an explicit
separate command because it requires a real, disposable PostgreSQL service. It
fails if that service is missing; it does not silently skip its checks.

## Run locally

Install the Python development requirements and start Docker. Create a disposable
PostgreSQL 17 container, bound only to loopback, with fictional test credentials:

```powershell
docker run --detach --rm --name macromate-postgres-test --env POSTGRES_USER=macromate_test --env POSTGRES_DB=macromate_test --env POSTGRES_PASSWORD=disposable-local-password --publish 127.0.0.1:55432:5432 postgres:17
docker exec macromate-postgres-test pg_isready -U macromate_test -d macromate_test
```

Wait until `pg_isready` reports that connections are accepted, then run:

```powershell
$env:APP_ENV = 'testing'
$env:TEST_POSTGRES_URL = 'postgresql://macromate_test:disposable-local-password@127.0.0.1:55432/macromate_test'
.\.venv\Scripts\python -m pytest tests/postgresql
```

After testing, stop the container you created and clear the process settings:

```powershell
docker stop macromate-postgres-test
Remove-Item Env:TEST_POSTGRES_URL
Remove-Item Env:APP_ENV
```

Do not use production connection strings or existing application databases. The
fixture requires a loopback host and the database and user names `macromate_test`.
Each test creates a unique `macromate_test_` schema, restricts application
connections to that schema, runs the actual migrations, and drops only that schema
during cleanup. The container has no persistent volume and is removed when stopped.
An interrupted test process may leave schemas in this disposable database; stopping
the container removes the test data. No live migration or data-repair step belongs
in this suite.

## Coverage and CI

The `PostgreSQL 17 integration` job in the quality workflow provisions its own
health-checked PostgreSQL 17 service with disposable credentials. It explicitly
runs `python -m pytest tests/postgresql`. It covers:

- Fresh migration to revision `0002`, expected tables and the history index.
- Legacy email normalization, password invalidation and retained undated progress.
- Rejection of duplicate normalized emails without advancing the revision or
  modifying the original accounts.
- Foreign-key, weight and calorie constraint enforcement through real PostgreSQL.
- OTP issuance and consumption across separate app instances, including replay
  rejection, with email delivery mocked.
- Login/logout, owned progress CRUD, cross-account rejection, undated-record
  ordering and database readiness.

This is PostgreSQL correctness coverage, not load testing, a concurrency proof,
backup/restore validation, or a production deployment rehearsal.

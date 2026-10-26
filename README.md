# MacroMate AI

A Flask application for formula-based nutrition estimates and personal progress
records. The name is retained, but there is no AI or machine learning model.

The calculator estimates daily calories, protein, carbohydrates and fats. Accounts
support email verification, password recovery, a private progress history, and an
administrator account directory. The frontend uses server-rendered Jinja templates,
local CSS, and small vanilla JavaScript modules.

## Run locally on Windows

Install Python 3.12, PostgreSQL 17 or a compatible maintained PostgreSQL release,
and Node.js 24 LTS for frontend development checks. Run from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

If `.venv` already exists, reuse it. If `.env` already exists, edit it instead of
copying over it. Keep `.env` local and untracked.

Create a dedicated local database and account using PostgreSQL's `psql` console:

```sql
CREATE ROLE macromate WITH LOGIN PASSWORD 'replace-with-your-local-password';
CREATE DATABASE macromate OWNER macromate;
```

Set `DATABASE_URL` in `.env` to the matching connection string:

```text
DATABASE_URL=postgresql://macromate:your-url-encoded-password@localhost:5432/macromate
APP_ENV=development
```

Percent-encode special characters in a URL password. Generate a secret and put the
result into `SECRET_KEY` in `.env`:

```powershell
.\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
```

For a **new, empty database**, apply migrations and start the development server:

```powershell
.\.venv\Scripts\python -m flask --app app:create_app db upgrade
.\.venv\Scripts\python -m flask --app app:create_app run --debug
```

Open **http://127.0.0.1:5000**. The calculator works without an account. Registration
and recovery require working SMTP settings. Debug mode is for local development.
For an existing installation, stop writes, take an encrypted backup and verify a
restore before running schema commands. Rehearse changes on that restored copy.
Inspect the baseline in `migrations/versions/0001_legacy.py` and the security
migration in `migrations/versions/0002_security.py` and retry-identity migration in
`migrations/versions/0003_progress_requests.py`; never stamp an unmatched schema
or recreate existing tables. Resolve duplicate normalized emails, orphaned progress
and invalid values through reviewed data repair. Verify revision `0003`, row counts,
ownership and authentication before reopening writes. Legacy plaintext passwords
require email recovery after migration.

### Optional local services with Docker Compose

Instead of installing PostgreSQL and creating the local role/database manually,
use Docker with a current Compose plugin. Edit the Compose settings already in
your local `.env`: replace `POSTGRES_PASSWORD` and `REDIS_PASSWORD` with strong
local passwords. `POSTGRES_USER` and `POSTGRES_DB` default to `macromate`.
Single-quote env-file values containing literal dollar signs or spaces.

```powershell
docker compose --env-file .env -f compose.yaml up -d --wait
docker compose --env-file .env -f compose.yaml ps
```

This starts PostgreSQL 17 and password-protected Redis 8. Only loopback ports are
published: `127.0.0.1:55432` and `127.0.0.1:56379`. If occupied, set `POSTGRES_PORT`
and/or `REDIS_PORT` in `.env`, and update the application's URLs to match. For the
default ports, set the following, substituting percent-encoded passwords:

```text
DATABASE_URL=postgresql://macromate:URL_ENCODED_POSTGRES_PASSWORD@127.0.0.1:55432/macromate
RATELIMIT_STORAGE_URI=redis://:URL_ENCODED_REDIS_PASSWORD@127.0.0.1:56379/0
```

Flask still runs on the host. Generate `SECRET_KEY`, configure SMTP, explicitly
apply migrations to a new database and start Flask as described above. Compose
does not start the app, send email or run schema commands. Health checks establish
service availability; they do not establish application migration readiness.
This is a local development stack, with no production TLS, backup or rollout setup.

To stop and remove the service containers while retaining data:

```powershell
docker compose --env-file .env -f compose.yaml down
```

Project-scoped named volumes retain PostgreSQL data and Redis append-only files
when containers are recreated. Keep the same project name when restarting.
`down --volumes` deletes that project's stored data; use ordinary `down` to keep it.
PostgreSQL's initialization credentials only apply to an empty data volume: changing
`.env` does not change an existing database password, role or database name. Rotate
existing credentials through PostgreSQL and update the app configuration together.
See the [PostgreSQL image reference](https://hub.docker.com/_/postgres) and
[Compose teardown reference](https://docs.docker.com/reference/cli/docker/compose/down/).

After installing Python dependencies, run the repeatable service check:

```powershell
.\.venv\Scripts\python scripts/check_compose.py
```

It requires a local Docker socket and Compose with `up --wait` support. It uses an
explicit temporary env file with fictional credentials, a unique project and random
loopback ports; it does not load your `.env`. The check rejects wrong PostgreSQL
passwords and missing/wrong Redis passwords, writes markers, recreates both
containers and verifies the markers survived. It validates project ownership and
storage identities before deleting only its own test containers, network and volumes.
No existing application database is migrated or inspected. CI runs this separately
from the offline gate; persistence across graceful recreation is not a backup or
crash-recovery guarantee.

## Email verification

Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`,
`MAIL_PASSWORD`, and `MAIL_DEFAULT_SENDER` in `.env`. Use a provider-issued app
password where required. TLS defaults to enabled on port 587. Codes expire after
`OTP_EXPIRY_SECONDS` (default 300) and resends have a server-side cooldown
(`OTP_COOLDOWN_SECONDS`, default 60).

Finish registration by submitting the code and the password you want to use.
`POST /api/auth/verify-otp` requires `email`, `otp`, and a `password` of 12–128
characters. The password chosen during email verification replaces any unverified
signup credentials. The verification form includes this field; API clients must
send it too. Invalid passwords do not consume a valid verification code.

**Revoke and rotate the SMTP app password previously committed to this repository.**
It has been removed from current source, but old history was preserved. Never reuse
that credential. Mail transport tests use mocks; no real email credentials are
needed to run tests.

## Development checks

```powershell
npm ci
npm run test:frontend
npm run lint
npm run format:check
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m ruff format --check .
.\.venv\Scripts\python -m pytest
```

Or run the complete gate after installing both dependency sets:

```powershell
.\.venv\Scripts\python scripts/check.py
```

`npm run format` formats JavaScript, CSS, tooling JSON, and this README. Templates
remain Jinja source and are not passed to ESLint or an incompatible HTML formatter.
There is no frontend build step or TypeScript dependency. The default Python suite
uses isolated SQLite databases. A separate PostgreSQL 17 integration job runs real
migrations, constraint checks, persisted OTP and owned progress tests. To run it
locally, set `APP_ENV=testing` and `TEST_POSTGRES_URL` to a disposable loopback
PostgreSQL database whose user and database are both named `macromate_test`, then
run `python -m pytest tests/postgresql`. Each test owns a unique schema and drops
only that schema. Never point this suite at an existing application database.

PostgreSQL OTP tests use separate app instances and connections to exercise real
account-row contention. They verify one-time verification/password resets,
concurrent failed-attempt budgets and a shared resend cooldown with one mocked
delivery. Database lock observation and bounded waits make the intended contention
explicit; this is scoped regression coverage rather than a general load test or
proof of provider delivery. No SMTP service is contacted by these tests.

A separate Redis 8 job verifies rate limits across independent application
processes, namespace isolation and safe storage-failure responses. For local use,
set `APP_ENV=testing` and `TEST_REDIS_URL` to a disposable unauthenticated loopback
Redis database 15, such as `redis://127.0.0.1:6379/15`, then run
`python -m pytest tests/redis`. Tests use random namespaces and never flush the
database. Both service suites fail rather than skip when configuration is missing.

The default suite also covers SMTP failure handling and auth/OTP transaction
rollback with safe retries. Mail transport is mocked; these tests do not establish
provider delivery or atomicity between database commits and SMTP acceptance.

`npm run test:frontend` uses Node's built-in runner for API requests and pagination.
Fetch and the minimal DOM are mocked; tests cover CSRF/credentials, JSON response
handling, network failures, aborts, failed-page retries and post-save refreshes.
Navigation retains the displayed page until its replacement loads successfully.
Tests run in the complete local/CI quality gate, alongside ESLint and
Prettier checks for the test sources. They do not replace real-browser testing.

The separate `npm run test:browser` suite exercises keyboard focus across sign-in,
calculation, progress, verification actions and administration pages, with real
sign-in and CSRF-protected requests. Install the matching
browser with `npx playwright install chromium`, set `PYTHON_EXECUTABLE` to your
virtual environment's Python executable, and run the suite. Linux may require
`npx playwright install --with-deps chromium` for system dependencies. The fixture
uses fictional owner/admin accounts, seeded pagination data, an in-memory database
and a dynamic loopback port. Service failures are intercepted; no SMTP or production
service is required. Tests cover preserving disabled states and user-moved focus,
restoring usable controls at page boundaries, and focusing the section heading
when navigation disappears. Its separate CI job runs alongside the default gate.
This is scoped Chromium coverage, not a full accessibility or assistive-technology
audit. Run a focused group with `npm run test:browser -- --grep "form loading"`,
`--grep "manual actions"` or `--grep "pagination:"`; run the full suite before a PR.

GitHub Actions runs the same quality gate on pull requests targeting `main` and
pushes to `main` or `dev`, using Python 3.12 and Node 24 on Linux. It can also be started
manually from the Actions tab. The workflow uses isolated test databases and no
application secrets. Repository owners configure required checks and review rules
separately; adding the workflow does not enable branch protection.

Run vulnerability checks separately from the offline quality gate:

```powershell
.\.venv\Scripts\python scripts/audit.py
```

This requires network access. PyPA `pip-audit` resolves `requirements-dev.txt`,
including the runtime requirements and transitive dependencies, and checks known
advisories. `npm run audit:check` audits the committed lockfile, including development
tools, and fails on low-or-higher severity findings. Neither command applies fixes
or suppresses advisories. CI runs these audits on PRs, main pushes and a weekly
schedule. A service outage fails the check; it is not a clean audit. Requirement
ranges are resolved at audit time, so deployed environments still need their own
dependency inventory and audit after installation.

## Architecture

```text
app/
  __init__.py          application factory; no startup schema mutation
  config.py           environment validation and cookie defaults
  extensions.py       database, migrations, CSRF and rate limiting
  errors.py           safe HTTP/API errors and rollback
  security.py         live account and role checks
  models/             users, progress, persisted OTP challenges
  repositories/       SQLAlchemy queries and ownership filters
  services/           authentication, email, formulas and tracking operations
  routes/             authentication, calculator, tracking, admin, health and pages
  utils/              validation
  templates/          shared layout and feature pages
  static/             local CSS and page-specific JavaScript
backend/app.py        compatibility entry point for backend.app:app
migrations/           Alembic baseline and forward security migration
tests/                isolated unit, integration and security tests
scripts/check.py      repeatable local quality gate
scripts/audit.py      network-backed Python and npm vulnerability checks
README.md             application setup, checks and deployment boundaries
```

PostgreSQL is the primary application database. The old local SQLite binary is
ignored and is not loaded by the application. Progress is scoped to the logged-in
account and supports creation, editing, deletion, and 20-record history pages.
Historical records with unknown dates are retained and sorted after dated records.

The progress view supports inclusive **From date** and **Through date** filters
using UTC dates. Apply dates to start at the first matching page; clear dates to
restore the complete history. Any date bound excludes legacy entries with unknown
dates. Unsaved entry fields are independent of history filters and downloads.

**Download CSV** exports all matching owned records, across history pages, with
`date_utc`, `weight_kg` and `calories_kcal` columns. Without date filters it retains
undated entries with an empty date cell. Exports are limited to 10,000 rows; narrow
the date interval if the limit is reached. The server returns an error instead of
silently truncating the file. CSV files contain personal progress data in plain
text; store downloaded copies accordingly. This export is not a database backup.
Authenticated API clients can use `GET /api/tracker/history` and
`GET /api/tracker/export.csv` with optional `date_from=YYYY-MM-DD` and
`date_to=YYYY-MM-DD` query parameters. Reversed, invalid and future bounds return
a validation error. Both routes enforce the current account's ownership.

The dashboard's recent summary covers 30 inclusive UTC dates ending today and can
be refreshed independently of the latest-entry panel. Averages are per stored
entry, so multiple records on one day count separately. Weight change compares the
first and last dated records, with record ID breaking same-date ties; fewer than
two dated records produces no change estimate. These statistics describe records
and are not a medical interpretation. `GET /api/tracker/summary` accepts the same
optional date bounds. An unfiltered summary includes undated rows in counts and
averages, while dated counts and weight changes exclude them. Empty averages and
insufficient changes are JSON `null`, not zero. The database computes the summary
in one statement so its aggregates and edge records share a read snapshot.

Progress creation accepts an optional canonical UUID `request_key`. Repeating a
create with the same owner, key and normalized date/weight/calories returns the
existing record; reusing a key for different values returns HTTP 409. Keys are
unique per owner and retained for the record's lifetime. Deleting a record removes
its request identity too. Clients omitting a key keep the original create behavior.
The browser reuses a key for unchanged retries within the current page, starts a
new key for changed values, and clears it after a successful/reset form. It does
not persist create intent across page reloads. This protects retrying a save whose
response was lost; it is not a general exactly-once delivery guarantee. Apply
migration `0003` before deploying the request-identity model. Development and CI
exercise migrations only on disposable databases, never a configured live URL.

## Configuration and deployment

[.env.example](.env.example) lists all supported environment settings. Key settings:

| Variable                | Purpose                                                                              |
| ----------------------- | ------------------------------------------------------------------------------------ |
| `APP_ENV`               | `development` by default; use `production` for deployment                            |
| `SECRET_KEY`            | Random session/OTP signing key; at least 32 characters in production                 |
| `DATABASE_URL`          | PostgreSQL connection string; required at startup                                    |
| `PGCONNECT_TIMEOUT`     | Optional libpq per-host connection timeout override; app default is five seconds     |
| `MAIL_*`                | SMTP transport and sender configuration                                              |
| `OTP_EXPIRY_SECONDS`    | Verification/reset code lifetime                                                     |
| `OTP_COOLDOWN_SECONDS`  | Minimum resend interval per account                                                  |
| `RATELIMIT_STORAGE_URI` | `memory://` locally; shared `redis://` or `rediss://` storage required in production |
| `TRUSTED_HOSTS`         | Comma-separated hostnames; required in production                                    |
| `LOG_LEVEL`             | Application logging level; defaults to `INFO`                                        |

Production requires PostgreSQL, strong secrets, TLS SMTP, trusted hosts and shared
Redis rate-limit storage. Session cookies are HTTP-only, SameSite=Lax, and secure
in production, with an eight-hour lifetime. Password resets revoke earlier account
sessions. All browser mutations, including JSON requests, require a CSRF token.
Redis storage errors fail closed with a generic HTTP 503; requests do not fall
back to a per-process limit or bypass rate limiting during an outage.

`APP_ENV` accepts exactly `development`, `testing` or `production`; an unknown mode
fails at startup. The mode supplied to `create_app({...})` takes precedence over
the shell environment and selects both cookie defaults and startup safeguards.
Selecting production through the factory enforces the same requirements as the
environment variable. An explicit testing mode keeps isolated local defaults.

`MAIL_PORT` must be an integer from 1 to 65535. `OTP_EXPIRY_SECONDS` must be a
positive integer, and `OTP_COOLDOWN_SECONDS` must be nonnegative; zero explicitly
disables the resend cooldown. The default OTP attempt budget is five; a factory
`OTP_MAX_ATTEMPTS` override must be positive. Numeric settings are validated after
factory overrides, so a valid override can replace a malformed shell value.
Invalid settings fail at startup with the setting name, without echoing its value.

Redis storage defaults to two-second connection/read timeouts with no automatic
retries. Factory `RATELIMIT_STORAGE_OPTIONS` can override individual defaults;
Redis URL query options take precedence for their driver fields. These are I/O
timeouts, not universal request deadlines or bounds on DNS and cluster failover.

New PostgreSQL connections default to a five-second per-host handshake timeout.
An explicit `connect_timeout` in `DATABASE_URL`, the libpq `PGCONNECT_TIMEOUT`
environment variable, or factory `SQLALCHEMY_ENGINE_OPTIONS["connect_args"]`
preserves the operator's setting. Factory connection arguments retain their normal
precedence over URI/environment values; caller dictionaries are not modified.
SQLite receives no PostgreSQL options. Explicit zero or negative libpq timeout
settings disable the timeout. This does not bound SQL query execution, waiting
for a pooled connection, DNS lookup or the total time spent trying multiple hosts.
The default suite tests API/HTML/readiness responses against an owned silent
loopback endpoint using the actual driver; no existing database is paused.
See [PostgreSQL's connection parameter reference](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-CONNECT-TIMEOUT).

Run Gunicorn on Linux with a separately configured HTTPS ingress:

```sh
gunicorn --bind 0.0.0.0:8000 'app:create_app()'
```

Gunicorn is not a Windows development server. Do not deploy Flask's debug server.
A non-root Dockerfile and disposable lifecycle check are available. With Docker
running, execute `python scripts/check_container.py` to build an isolated image and
verify runtime dependencies, non-root/read-only execution, health, assets, missing
configuration refusal and SIGTERM. The check removes only its own containers and
image tag. The image defaults to production configuration and leaves schema
migrations as explicit operator actions. Never bake local secrets into the image;
keep `127.0.0.1` in `TRUSTED_HOSTS` for its internal liveness probe.
The app does not trust forwarded proxy headers automatically. Configure a trusted
proxy and worker count for your deployment. `/health/live` checks process liveness;
`/health/ready` checks that the required user, progress and OTP tables and model
columns can be queried, without reading their data or disclosing connection details.
An empty or outdated schema returns 503; health checks never create or migrate it.
Readiness does not verify SMTP, Redis, write permissions, constraints or the installed
Alembic revision. Apply and verify migrations separately before deployment.

## Security, operations and limitations

- Passwords use Werkzeug scrypt hashes. Legacy plaintext credentials never log in;
  recovery by email is required after migration.
- OTPs use cryptographic random generation, keyed hashes in the database, expiry,
  attempt limits, cooldowns, and one-time consumption. User row locks coordinate
  issuance and verification on PostgreSQL.
- APIs use safe ORM queries, ownership checks, bounded pagination, transaction
  rollback, and generic service-failure responses.
- Security headers use a same-origin CSP without inline scripts. Secrets and OTPs
  are not intentionally logged by the application.
- Registration/resend/reset responses are generic. Delivery failures and response
  timing can still distinguish some account states; full enumeration resistance
  is not claimed.
- The nutrition formula does not account for height, activity, age, pregnancy or
  medical conditions. Estimates are not medical advice.
- Keep encrypted database backups and verify restores on an isolated database
  before deployment. Never run destructive schema recreation on existing data.
- Administrator access requires a verified account whose database role is `admin`.
  No public route can promote an account. Grant that role only through an audited
  operator procedure.
- Local PostgreSQL/Redis composition is available for development. A production
  rollout remains outstanding; container/service checks do not establish production
  readiness.

## Troubleshooting

- **DATABASE_URL must be configured:** create/edit `.env` in the repository root.
- **Database unavailable:** check PostgreSQL is running, the database/user exists,
  connection credentials are correct, and migrations have been applied.
- **Old account cannot log in:** reset its password by email after migration.
- **Email delivery unavailable:** check SMTP credentials, sender, TLS and provider
  restrictions. Never paste an app password into a bug report.
- **Session expired / CSRF error:** reload the page and retry; signing in or out
  replaces the session. Keep `APP_ENV=development` for plain-HTTP local access.
- **Port 5000 in use:** add `--port 5001` to the Flask run command.
- **pytest cache or temporary-folder permissions:** run with a writable temporary
  directory or correct its filesystem permissions; do not disable failing tests.

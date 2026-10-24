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
For an existing installation, follow [the migration guide](docs/migrations.md)
before running schema commands.

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

`npm run format` formats JavaScript, CSS, tooling JSON, and documentation. Templates
remain Jinja source and are not passed to ESLint or an incompatible HTML formatter.
There is no frontend build step or TypeScript dependency. The default Python suite
uses isolated SQLite databases. A separate PostgreSQL 17 integration job runs real
migrations, constraint checks, persisted OTP and owned progress tests. See
[PostgreSQL test setup](docs/postgresql-testing.md) for the explicit local command
and disposable database requirements, and [validation notes](docs/validation.md)
for earlier verification records.

GitHub Actions runs the same quality gate on pull requests targeting `main` and
pushes to `main`, using Python 3.12 and Node 24 on Linux. It can also be started
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
docs/                 migration, architecture roadmap and validation notes
```

PostgreSQL is the primary application database. The old local SQLite binary is
ignored and is not loaded by the application. Progress is scoped to the logged-in
account and supports creation, editing, deletion, and 20-record history pages.
Historical records with unknown dates are retained and sorted after dated records.

## Configuration and deployment

[.env.example](.env.example) lists all supported environment settings. Key settings:

| Variable                | Purpose                                                                              |
| ----------------------- | ------------------------------------------------------------------------------------ |
| `APP_ENV`               | `development` by default; use `production` for deployment                            |
| `SECRET_KEY`            | Random session/OTP signing key; at least 32 characters in production                 |
| `DATABASE_URL`          | PostgreSQL connection string; required at startup                                    |
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

Run Gunicorn on Linux with a separately configured HTTPS ingress:

```sh
gunicorn --bind 0.0.0.0:8000 'app:create_app()'
```

Gunicorn is not a Windows development server. Do not deploy Flask's debug server.
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
- Dockerfile/Compose and a production rollout are
  still outstanding from the broader engineering roadmap. This checkout is not
  claimed to be production-ready.

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

# Validation record

Validated locally on 24 October 2026 with Python 3.12.10 and Node.js 24.19.0.
The seven-commit follow-up starts after
`ce71112d2161a73693167592f0604c8bd2716d1b` on the user-approved `main` branch.

## Passed automated checks

- `npm ci`: lockfile installation succeeded; npm reported zero known vulnerabilities
  in its dependency set at install time.
- `python scripts/check.py`: Ruff linting and formatting, **95 pytest cases**,
  ESLint, and Prettier checks passed. Run this with the project's virtualenv Python.
- Isolated tests cover formulas and numeric boundaries, registration hashing,
  login/logout, session revocation, OTP expiry/attempts/cooldown/single use,
  password recovery, CSRF, owner-only progress CRUD, admin authorization,
  page/static rendering, configuration and migration behavior.
- A new history-order test keeps undated legacy records after dated records.
- A configuration regression test covers `postgres://`, `postgresql://`, and
  explicit `postgresql+psycopg2://` URLs. Driver selection is explicit because
  current SQLAlchemy defaults can differ from the installed database driver.

The general pytest suite uses in-memory or temporary SQLite databases and no live
email credentials. Initial sandbox runs hit filesystem access errors for pytest
cache/temp directories; the complete rerun with authorized directory access passed.
No test was disabled or weakened to bypass those errors.

## PostgreSQL integration

An isolated PostgreSQL 17 Docker container was created with fictional accounts,
ephemeral credentials, and a random port bound only to loopback. Checks passed for:

- Fresh migrations through revision `0002`.
- Legacy baseline upgrade, normalized email, plaintext password invalidation,
  retained progress count, and unknown historical dates.
- OTP issuance in one app instance and consumption in another, including replay
  rejection.
- Login, logout, progress creation, update, deletion, owner enforcement, history
  ordering, and database readiness.

The temporary container was stopped and removed. No existing application database
or user data was migrated. SMTP was mocked; real provider delivery remains untested.
These integration checks were executed with a local test harness and do not yet
constitute a hosted PostgreSQL CI job.

## Browser verification

Installed Chrome ran headlessly against an isolated loopback test server. The
browser completed 18 public-page layout checks across 390, 768 and 1440 pixel
widths without horizontal overflow. It also completed:

- Calculator submission and the expected 2,310 kcal maintenance result at 70 kg.
- Registration, mocked email OTP verification, and login.
- Progress entry creation, editing and confirmed deletion.
- Rejection of a non-admin at the admin page, logout, and password reset.
- Admin login and directory loading.

No uncaught page JavaScript errors were observed. Desktop and mobile screenshots
were inspected locally. Browser artifacts and fictional test mail stayed in the
ignored work directory. This is practical smoke coverage, not a full WCAG audit,
a cross-browser matrix, or a performance benchmark.

## Intentional compatibility changes

- `/` is the landing page; the login page is `/login`.
- Signup, resend and reset-request APIs return generic 202 responses.
- Tracking mutations require authentication and an explicit date. Supplied email
  fields no longer choose the owner.
- `/api/tracker/get/<email>` remains available only for the authenticated owner's
  email and returns the same paginated envelope as `/api/tracker/history`:
  `records`, `page`, `pages`, and `total`.
- Calculator results retain two decimal places rather than truncating each macro
  independently. Unsupported goals and invalid weights now return validation errors.

## Hosted quality checks

The `Quality` GitHub Actions workflow now runs the existing `scripts/check.py`
gate for pull requests targeting `main`, pushes to `main`, and manual runs. It uses
Python 3.12 and Node 24 on Linux, read-only repository permissions, pinned action
commits, and isolated SQLite tests without production secrets. Its actual run
results are available in the repository's Actions tab and individual PR checks.
This automates the local quality gate; PostgreSQL service testing and dependency
auditing remain separate roadmap items.

## Outstanding work

The broader production roadmap remains incomplete: Docker/Compose packaging,
PostgreSQL CI, Python dependency auditing, Redis operational testing, live mail delivery,
backup/restore rehearsal, and a production rollout have not been verified here.
Gunicorn has not been started on this Windows host. Production startup requires
real infrastructure and secrets; do not deploy with example placeholders.

Revoke and rotate the previously exposed SMTP app password. Source cleanup does
not revoke a credential or remove it from historical commits. No pushes were made
by the agent.

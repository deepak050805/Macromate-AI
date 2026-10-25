# Browser keyboard regression tests

The progress-history suite uses Playwright with Chromium to exercise real focus,
native confirmation dialogs, sign-in, CSRF-protected requests and history updates.
It runs separately from the default Python/Node quality gate because it requires
a browser executable and an available loopback socket.

## Local setup

Install the Python development requirements and the committed npm dependencies,
then install Playwright's matching Chromium build:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
npm ci
npx playwright install chromium
$env:PYTHON_EXECUTABLE = (Resolve-Path .venv/Scripts/python.exe).Path
npm run test:browser
```

On Linux, use `npx playwright install --with-deps chromium` to install system
dependencies too. Set `PYTHON_EXECUTABLE` to the virtual environment's Python
executable, or activate that environment so the default `python` resolves to it.
Browser downloads and system-package installation require network access.

An installed Chrome can be used locally instead of downloading Chromium:

```powershell
$env:BROWSER_CHANNEL = 'chrome'
npm run test:browser
Remove-Item Env:BROWSER_CHANNEL
```

CI leaves `BROWSER_CHANNEL` unset and installs the browser version matching the
lockfile. The separate **Chromium keyboard and progress UI** workflow job runs on
Ubuntu 24.04 with Python 3.12 and Node 24. It uses no application secrets.

## Fixture isolation

Playwright starts a dedicated Flask fixture on `127.0.0.1` with an operating-system
assigned port. Its published URL is captured from stdout, and tests reject URLs
outside that loopback pattern. An existing development server is never reused.

The fixture creates an in-memory SQLite schema and a fictional verified owner.
It overrides the database, session signing key, mail credentials and trusted hosts.
Rate limiting is disabled for deterministic interaction tests; CSRF remains
enabled. Tests sign in through the real form and save progress through the real
API. No production database, Redis service or SMTP connection is needed.

Tests run with one worker and unique entry dates. Each test receives a fresh
browser context; the fixture's in-memory records are shared within that run and
discarded when the server exits. Playwright stops its fixture after the run.
Failure context and other local output go under ignored
`.task-work/browser-results/`.

## Covered behavior and limits

- Verified-owner sign-in and progress creation through the CSRF-protected UI.
- Keyboard cancellation resets the edit form and returns focus to Weight.
- Successful deletion returns focus to the history heading. Its `tabindex="-1"`
  allows programmatic focus without adding a stop to ordinary Tab navigation.
- Failed deletion re-enables and restores focus to the initiating action.
- A user who moves focus elsewhere during deletion keeps that focus.
- Dismissing confirmation retains the entry and focused action.

The failed-delete case intercepts only the DELETE response. The pending-delete
case delays the real request to exercise focus movement. Other requests reach the
isolated application. Existing backend tests cover ownership and error handling.

These are focused Chromium regressions, not a complete WCAG audit. They do not
establish screen-reader behavior, responsive layouts, other browser behavior or
production-service reliability. Run `python scripts/check.py` separately for the
default Python/Node tests and lint/format checks.

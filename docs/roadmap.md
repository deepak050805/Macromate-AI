# Implementation roadmap

Baseline: `25d5582417294a49757cf8fa9444492778d9199e`, branch `dev`.
The initial working tree was clean. No remote writes are authorized.

Verified defects: hardcoded SMTP credential, plaintext password persistence,
OTP disclosure in logs and worker-local storage, unauthenticated progress writes
and reads, PostgreSQL queries with SQLite placeholders, missing connection cleanup,
default application secrets, import-time schema changes, unvalidated calculator
inputs, duplicated inline UI assets, and no test or migration framework.
A database binary is tracked; local database contents must never be printed.

Implementation sequence:
1. Remove credentials and isolate local artifacts; constrain dependencies.
2. Establish app factory, feature routes, services, repositories and models.
3. Harden authentication, OTP delivery, sessions, CSRF and authorization.
4. Add non-destructive migrations, safe legacy-account recovery and tracking CRUD.
5. Preserve validated nutrition formulas with consistent energy totals.
6. Redesign shared layouts and individual pages with accessible vanilla assets.
7. Add regression coverage, lint/format tooling, containers and CI.
8. Document setup, operations, migration and limitations; audit the final history.

Each coherent change receives its own verified Conventional Commit. Target:
exactly 100 commits after the baseline. Record actual progress using
`git log --reverse --oneline 25d5582417294a49757cf8fa9444492778d9199e..HEAD`.
Do not manufacture commits or claim unrun checks passed.

Credential response: rotate the previously committed SMTP app password with the
provider immediately. Old history is preserved, so revocation is mandatory.
No existing data will be deleted and no migrations run against a live database.

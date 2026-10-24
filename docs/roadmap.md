# Engineering roadmap

This roadmap describes the current application and prioritizes independent,
testable improvements. Each change uses a feature branch, validated commit and
pull request targeting `main`. Commit or PR counts are not acceptance criteria.

## Delivered foundation

- Flask application factory, feature routes, services, ORM repositories and models.
- Hashed passwords, persistent keyed OTP challenges, recovery, session revocation,
  CSRF, rate limiting, owner-scoped tracking and administrator authorization.
- Fresh and legacy migrations that retain undated historical progress records.
- Shared responsive templates and local JavaScript for authentication, calculator,
  progress history, dashboard and administration.
- Local quality gate for Python tests, Ruff, ESLint and Prettier.
- Pagination conversion regression fix, verified in merged
  [PR #1](https://github.com/deepak050805/Macromate-AI/pull/1).
- GitHub Actions quality workflow for PRs to `main`, pushes to `main`, and manual
  runs. It executes the same local gate on Python 3.12 and Node 24, with pinned
  actions, read-only repository permissions and no application secrets.

## Prioritized outstanding work

1. **Dependency auditing:** run supported Python and npm audits, resolve actionable
   vulnerabilities, and add repeatable CI checks without blanket suppressions.
2. **PostgreSQL CI:** commit isolated integration coverage for fresh and legacy
   migrations, cross-app OTP persistence, and owned progress CRUD on PostgreSQL 17.
   Existing SQLite tests and the earlier manual PostgreSQL rehearsal do not replace
   a hosted database integration job.
3. **Redis and reliability:** verify shared rate-limit behavior and service-failure
   handling; add evidence-based rollback and safe error regression tests.
4. **Accessibility:** automate relevant keyboard, form feedback and responsive
   interaction checks, building on the recorded browser smoke tests.
5. **Packaging:** inspect deployment needs, then validate a non-root container,
   startup command, health checks and local service composition.
6. **Operations:** rehearse encrypted backup/restore, verify real mail delivery,
   configure deployment infrastructure, and validate a production rollout.

Each item must have a concrete problem, acceptance criteria and actual validation
before it is considered delivered. A successful quality workflow does not establish
production readiness or enforce branch protection by itself. Required checks and
independent-review policies are repository settings managed by the owner.

## Owner or infrastructure dependencies

- Revoke and rotate the SMTP app password previously exposed in Git history.
  Removing it from current source did not revoke it. Do not print old credentials.
- Production secrets, SMTP access, database/Redis hosting, backups and rollout
  require separately authorized infrastructure work.
- Do not migrate live data or execute destructive downgrades as part of CI.

Historical local verification and its limits are recorded in
[validation notes](validation.md); safe schema adoption is described in the
[migration guide](migrations.md).

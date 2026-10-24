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
- Repeatable Python requirement and npm lockfile audits, with CI enforcement on
  PRs, main pushes and a weekly schedule. Both include development dependencies
  and fail on advisory findings or service errors without blanket exclusions.
- Separate PostgreSQL 17 integration suite and hosted service job for fresh and
  legacy migrations, duplicate-email rejection, database constraints, cross-app
  OTP persistence, progress ownership and CRUD. Tests use unique disposable schemas.

## Prioritized outstanding work

1. **Redis and reliability:** verify shared rate-limit behavior and service-failure
   handling; add evidence-based rollback and safe error regression tests.
2. **Accessibility:** automate relevant keyboard, form feedback and responsive
   interaction checks, building on the recorded browser smoke tests.
3. **Packaging:** inspect deployment needs, then validate a non-root container,
   startup command, health checks and local service composition.
4. **Operations:** rehearse encrypted backup/restore, verify real mail delivery,
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

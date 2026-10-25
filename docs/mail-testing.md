# Email failure and retry coverage

The default quality gate includes two complementary suites:

- `tests/unit/test_mail_delivery.py` verifies TLS with certificate/hostname checks
  before authentication, sender fallback, missing-credential refusal, and generic
  exceptions/logs for failures during connection, context entry/exit, TLS, login
  and message submission. Every SMTP object is mocked.
- `tests/integration/test_mail_rollback.py` exercises the real auth, OTP, mail and
  error-handler paths on isolated SQLite databases with mocked SMTP delivery.
  Failed signup must leave no account or challenge; failed signup retry, resend
  and password-reset issuance must preserve the prior challenge fields, failed
  attempt count and account credentials. A later delivery and confirmation must
  succeed, demonstrating that no cooldown or broken session blocks recovery.
- `tests/postgresql/test_mail_rollback.py` uses real migrations and separate
  application instances to verify that failed signup leaves no persisted account,
  failed reset preserves the committed challenge, and another application can
  retry and confirm. It runs in the explicit PostgreSQL suite described in
  [PostgreSQL test setup](postgresql-testing.md), with mocked delivery and unique
  disposable schemas.

```powershell
.\.venv\Scripts\python -m pytest tests/unit/test_mail_delivery.py tests/integration/test_mail_rollback.py
```

All addresses, passwords and codes in these tests are fictional. No `.env` values
are needed, and no email is sent. The tests do not establish live provider access,
DNS, deliverability, PostgreSQL concurrency or production SMTP readiness.

SMTP and a database transaction are not atomic. A provider can accept a message
before a later transport or database failure; such a message may contain a code
that was rolled back, and a retry may send another message. These tests establish
safe application state after a surfaced transport failure, not exactly-once email
delivery. Use the latest successfully issued code after retrying.

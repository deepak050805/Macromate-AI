# Database migrations and account recovery

PostgreSQL is the primary database. The app never creates tables on import or
startup. Alembic revisions are managed with Flask-Migrate.

## New installation

Create an empty dedicated database, configure `.env`, then run:

```powershell
.\.venv\Scripts\python -m flask --app app:create_app db upgrade
.\.venv\Scripts\python -m flask --app app:create_app db current
```

The expected current revision is `0002`.

## Adopt an existing PostgreSQL installation

1. Stop writes and take an encrypted backup. Test restoring it to a separate
   database. Do all migration rehearsal on that copy first.
2. Inspect schema and data privately. Revision `0001` describes the original
   `users` table (id, email, password, is_verified, role) and `progress` table
   (id, email, weight, calories). Confirm these match before stamping. Never stamp
   a schema simply to bypass a migration error.
3. Resolve duplicate normalized emails, missing account emails, orphaned progress,
   null weights/calories, or out-of-range progress values through an explicit,
   reviewed data-repair procedure. No migration deletes those records for you.
4. On a confirmed baseline schema, mark that baseline without recreating tables:

   ```powershell
   .\.venv\Scripts\python -m flask --app app:create_app db stamp 0001
   .\.venv\Scripts\python -m flask --app app:create_app db upgrade
   ```

5. Confirm revision `0002`, verify row counts and ownership, exercise authentication
   and tracking, and only then reopen writes.

Revision `0002` normalizes emails, replaces recognizable plaintext/non-hash
passwords with a reset-required marker, adds account session versions and
creation timestamps, and creates persistent OTP challenges. It adds progress
relationships, indexes, and numeric constraints. Legacy dates remain NULL because
no trustworthy historical date exists; the user can set one when editing a record.
Creation timestamps for migrated records describe migration time, not original
record creation time.

Legacy accounts must use the password recovery page. A successful reset proves
email ownership, hashes the new password, and invalidates older sessions. Password
hashes already using supported Werkzeug scrypt/PBKDF2 prefixes are retained.
Changing the application secret invalidates signed sessions and outstanding OTPs.

Duplicate emails or invalid legacy data cause migration failure; PostgreSQL runs
these changes in a transaction. Investigate and repair the restore copy rather than
removing constraints or deleting live records. Destructive downgrades are explicitly
disabled. Recovery means restoring a verified backup, with a clear plan for writes
made after that backup. Do not run `drop_all` or `create_all` on an existing install.

Tests use `create_all` only for isolated empty test databases. Migration tests
separately exercise the real revision chain for fresh and legacy databases.

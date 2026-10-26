from app.extensions import db


def promote(app, email, **kwargs):
    return app.test_cli_runner().invoke(args=["accounts", "promote", "--email", email, "--yes"], **kwargs)


def test_operator_can_promote_a_verified_account_and_revoke_old_sessions(app, logged_in, account):
    version = account.auth_version
    result = promote(app, account.email)
    assert result.exit_code == 0
    db.session.refresh(account)
    assert account.role == "admin"
    assert account.auth_version == version + 1
    assert logged_in.get("/admin").status_code == 401


def test_promotion_never_verifies_a_pending_account(app, account):
    account.is_verified = 0
    db.session.commit()
    result = promote(app, account.email)
    assert result.exit_code != 0
    db.session.refresh(account)
    assert account.role == "user"
    assert account.is_verified == 0


def test_promotion_requires_explicit_confirmation(app, account):
    result = app.test_cli_runner().invoke(args=["accounts", "promote", "--email", account.email], input="n\n")
    assert result.exit_code != 0
    db.session.refresh(account)
    assert account.role == "user"


def test_repeated_promotion_is_a_noop(app, account):
    assert promote(app, account.email).exit_code == 0
    db.session.refresh(account)
    version = account.auth_version
    assert promote(app, account.email).exit_code == 0
    db.session.refresh(account)
    assert account.auth_version == version


def test_promotion_does_not_create_missing_accounts(app):
    result = promote(app, "missing-operator@example.test")
    assert result.exit_code != 0
    assert "Account not found" in result.output

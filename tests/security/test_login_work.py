from unittest.mock import Mock

from app.services import auth


def test_unknown_login_still_performs_one_real_password_verification(client, account, monkeypatch):
    verifier = Mock(wraps=auth.verify_password)
    monkeypatch.setattr(auth, "verify_password", verifier)
    password = "fictional wrong password"
    known = client.post("/api/auth/login", json={"email": account.email, "password": password})
    unknown = client.post(
        "/api/auth/login", json={"email": "absent@example.test", "password": password}
    )
    assert known.status_code == unknown.status_code == 401
    assert known.json == unknown.json
    assert verifier.call_count == 2
    known_hash, unknown_hash = [call.args[0] for call in verifier.call_args_list]
    assert known_hash.split("$", 1)[0] == unknown_hash.split("$", 1)[0]
    assert known_hash != unknown_hash

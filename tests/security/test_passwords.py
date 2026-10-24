from app.services.passwords import hash_password, verify_password


def test_hashing():
    first = hash_password("long enough password")
    second = hash_password("long enough password")
    assert first != second
    assert verify_password(first, "long enough password")
    assert not verify_password(first, "wrong password")


def test_legacy_rejected():
    for stored in [None, "plaintext", "!reset-required", "scrypt:broken", "pbkdf2:invalid"]:
        assert not verify_password(stored, "plaintext")

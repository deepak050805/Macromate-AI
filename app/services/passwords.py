from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password, method="scrypt")


def verify_password(stored, password):
    # Legacy plaintext never authenticates; recovery requires email ownership.
    if not isinstance(stored, str) or not stored.startswith(("scrypt:", "pbkdf2:")):
        return False
    try:
        return check_password_hash(stored, password)
    except (ValueError, TypeError):
        return False

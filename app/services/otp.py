import hashlib
import hmac
import secrets
import time
from flask import current_app
from app.extensions import db
from app.models import Otp
from app.services.mail import send_code
from app.utils.validation import ValidationError


def digest(user_id, purpose, code):
    key = current_app.secret_key.encode()
    return hmac.new(key, f"{user_id}:{purpose}:{code}".encode(), hashlib.sha256).hexdigest()


def issue(user, purpose):
    now = time.time()
    challenge = db.session.get(Otp, user.id)
    if challenge and now - challenge.sent_at < current_app.config["OTP_COOLDOWN_SECONDS"]:
        return False
    code = f"{secrets.randbelow(1000000):06d}"
    if not challenge:
        challenge = Otp(user_id=user.id)
        db.session.add(challenge)
    challenge.digest = digest(user.id, purpose, code)
    challenge.purpose = purpose
    challenge.expires_at = now + current_app.config["OTP_EXPIRY_SECONDS"]
    challenge.sent_at = now
    challenge.attempts = 0
    send_code(user.email, code)
    return True


def consume(user, purpose, code):
    challenge = db.session.get(Otp, user.id) if user else None
    valid = (isinstance(code, str) and len(code) == 6 and code.isascii() and code.isdecimal())
    if not challenge or challenge.purpose != purpose or challenge.expires_at <= time.time() or challenge.attempts >= current_app.config["OTP_MAX_ATTEMPTS"]:
        raise ValidationError("Code is invalid or expired; request a new code")
    challenge.attempts += 1
    if not valid or not hmac.compare_digest(challenge.digest, digest(user.id, purpose, code)):
        db.session.commit()  # Failed attempts must survive the error response.
        raise ValidationError("Code is invalid or expired; request a new code")
    db.session.delete(challenge)

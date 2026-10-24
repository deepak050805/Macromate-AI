import smtplib
import ssl
from email.message import EmailMessage
from flask import current_app


class DeliveryError(RuntimeError):
    pass


def send_code(email, code):
    config = current_app.config
    sender = config["MAIL_DEFAULT_SENDER"] or config["MAIL_USERNAME"]
    if not sender or not config["MAIL_USERNAME"] or not config["MAIL_PASSWORD"]:
        raise DeliveryError("Email delivery is unavailable")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = email
    message["Subject"] = "Your MacroMate verification code"
    message.set_content(f"Your code is {code}. It expires in {config['OTP_EXPIRY_SECONDS']} seconds. If you did not request it, ignore this email.")
    try:
        with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=10) as server:
            if config["MAIL_USE_TLS"]:
                server.starttls(context=ssl.create_default_context())
            server.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
            server.send_message(message)
    except (smtplib.SMTPException, OSError):
        current_app.logger.warning("mail_delivery_failed")
        raise DeliveryError("Email delivery is unavailable") from None

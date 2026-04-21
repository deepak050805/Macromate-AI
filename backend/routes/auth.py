import sqlite3
from flask import Blueprint, request, jsonify
from backend.models import connect
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

auth_bp = Blueprint("auth", __name__)

# ─────────────────────────────────────────────
# ✏️  PUT YOUR GMAIL CREDENTIALS HERE
# ─────────────────────────────────────────────
GMAIL_ADDRESS  = "macromate.ai@gmail.com"
GMAIL_APP_PASS = "yvnqueibgzgsbynt"    # ← your 16-char App Password
# ─────────────────────────────────────────────

if "your_gmail" in GMAIL_ADDRESS or "xxxx" in GMAIL_APP_PASS:
    print("[MacroMate] ⚠️  WARNING: SMTP credentials not set. OTP emails will fail.")

otp_store = {}
OTP_EXPIRY_SECONDS = 300


def send_otp_email(to_email: str, otp: str) -> bool:
    subject = "Your MacroMate Verification Code"
    body = f"""Hi there,

Your MacroMate one-time verification code is:

    {otp}

This code expires in {OTP_EXPIRY_SECONDS // 60} minutes.
If you did not request this, please ignore this email.

— MacroMate Team
"""
    msg = MIMEMultipart()
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        print(f"[MacroMate] Sending OTP to {to_email} via {GMAIL_ADDRESS}...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        print(f"[MacroMate] ✅ OTP sent successfully to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[MacroMate] ❌ SMTP auth failed — check GMAIL_ADDRESS and GMAIL_APP_PASS")
        return False

    except smtplib.SMTPRecipientsRefused:
        print(f"[MacroMate] ❌ Recipient refused: {to_email}")
        return False

    except smtplib.SMTPException as e:
        print(f"[MacroMate] ❌ SMTP error: {e}")
        return False

    except Exception as e:
        print(f"[MacroMate] ❌ Unexpected email error: {e}")
        return False


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Step 1 of registration.
    Inserts user as UNVERIFIED (is_verified=0) and sends OTP.
    User cannot log in until they verify their email.
    """
    data = request.json
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    conn = connect()
    c = conn.cursor()

    try:
        print(f"[MacroMate] Signup attempt for: {email}")

        # Check if user already exists and is verified — block them
        c.execute("SELECT is_verified FROM users WHERE email=?", (email,))
        row = c.fetchone()

        if row:
            if row[0] == 1:
                return jsonify({"message": "User already registered. Please login."}), 400
            else:
                # Unverified account exists — update password and resend OTP
                c.execute("UPDATE users SET password=? WHERE email=?", (password, email))
                conn.commit()
                print(f"[MacroMate] Re-sending OTP for unverified account: {email}")
        else:
            # Brand new user — insert as unverified
            c.execute(
                "INSERT INTO users (email, password, is_verified) VALUES (?, ?, 0)",
                (email, password)
            )
            conn.commit()
            print(f"[MacroMate] ✅ Unverified account created for: {email}")

        # Generate and store OTP
        otp = str(random.randint(100000, 999999))
        otp_store[email] = {
            "otp": otp,
            "expires_at": time.time() + OTP_EXPIRY_SECONDS
        }
        print(f"[MacroMate] OTP for {email}: {otp}")

        # Send OTP email
        success = send_otp_email(email, otp)
        if not success:
            otp_store.pop(email, None)
            return jsonify({"message": "Failed to send OTP email. Check server SMTP config."}), 500

        return jsonify({"message": "OTP sent", "email": email})

    except Exception as e:
        print(f"[MacroMate] ❌ Signup error: {e}")
        return jsonify({"message": "An unexpected error occurred. Please try again."}), 500
    finally:
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Only allows login if user is verified (is_verified=1).
    """
    data = request.json
    email = data.get("email", "").strip()
    password = data.get("password", "")

    conn = connect()
    c = conn.cursor()

    try:
        print(f"[MacroMate] Login attempt for: {email}")
        c.execute(
            "SELECT is_verified FROM users WHERE email=? AND password=?",
            (email, password)
        )
        user = c.fetchone()

        if not user:
            print(f"[MacroMate] Login failed — wrong credentials for: {email}")
            return jsonify({"message": "Invalid credentials"}), 401

        if user[0] == 0:
            print(f"[MacroMate] Login blocked — email not verified: {email}")
            return jsonify({"message": "Email not verified. Please complete OTP verification."}), 403

        print(f"[MacroMate] ✅ Login successful for: {email}")
        return jsonify({"message": "Login successful", "email": email})

    finally:
        conn.close()


@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    """
    Standalone OTP send (for resend functionality on otp.html).
    """
    data = request.json
    email = data.get("email", "").strip()

    if not email:
        return jsonify({"message": "Email is required"}), 400

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"message": "Invalid email address"}), 400

    otp = str(random.randint(100000, 999999))
    otp_store[email] = {
        "otp": otp,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS
    }

    print(f"[MacroMate] OTP (resend) for {email}: {otp}")
    success = send_otp_email(email, otp)

    if not success:
        otp_store.pop(email, None)
        return jsonify({"message": "Failed to send email. Check server SMTP config."}), 500

    return jsonify({"message": "OTP sent successfully"})


@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    """
    Verifies OTP and marks user as verified (is_verified=1).
    After this, the user can log in.
    """
    data = request.json
    email = data.get("email", "").strip()
    otp_entered = data.get("otp", "").strip()

    if not email or not otp_entered:
        return jsonify({"message": "Email and OTP are required"}), 400

    record = otp_store.get(email)

    if not record:
        return jsonify({"message": "OTP not found. Please request a new one."}), 404

    if time.time() > record["expires_at"]:
        del otp_store[email]
        return jsonify({"message": "OTP expired. Please request a new one."}), 401

    if otp_entered != record["otp"]:
        print(f"[MacroMate] Wrong OTP for {email}: entered {otp_entered}")
        return jsonify({"message": "Invalid OTP. Please try again."}), 401

    # OTP is valid — mark user as verified in DB
    del otp_store[email]

    conn = connect()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET is_verified=1 WHERE email=?", (email,))
        conn.commit()
        print(f"[MacroMate] ✅ Email verified and user activated: {email}")
    finally:
        conn.close()

    return jsonify({"message": "OTP verified", "email": email})

@auth_bp.route("/all-users", methods=["GET"])
def all_users():
    conn = connect()
    c = conn.cursor()
    try:
        c.execute("SELECT id, email, is_verified FROM users")
        users = c.fetchall()
    finally:
        conn.close()

    return jsonify({
        "users": [
            {
                "id": u[0],
                "email": u[1],
                "verified": bool(u[2])
            }
            for u in users
        ]
    })
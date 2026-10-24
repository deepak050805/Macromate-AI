from flask import Blueprint, redirect, render_template, url_for
from app.security import administrator, authenticated, current_user

bp = Blueprint("pages", __name__)


@bp.get("/")
def home():
    return render_template("home.html")


@bp.get("/login")
def login():
    if current_user():
        return redirect(url_for("pages.dashboard"))
    return render_template("auth/login.html")


@bp.get("/signup")
def signup():
    return render_template("auth/signup.html")


@bp.get("/otp")
def otp():
    return render_template("auth/otp.html")


@bp.get("/reset-password")
def reset():
    return render_template("auth/reset.html")


@bp.get("/dashboard")
@authenticated
def dashboard():
    return render_template("dashboard/index.html")


@bp.get("/calculator")
def calculator():
    return render_template("calculator/index.html")


@bp.get("/tracking")
@authenticated
def tracking():
    return render_template("tracking/index.html")


@bp.get("/admin")
@administrator
def admin():
    return render_template("admin/index.html")

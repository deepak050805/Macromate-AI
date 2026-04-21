import os
from flask import Flask, render_template
from flask_cors import CORS
from models import init_db
from routes.macros import macros_bp
from routes.auth import auth_bp
from routes.tracker import tracker_bp

app = Flask(__name__, template_folder="templates")
CORS(app)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "secret123")

app.register_blueprint(macros_bp, url_prefix="/api/macros")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(tracker_bp, url_prefix="/api/tracker")

# Initialize DB on every startup — safe to run repeatedly.
# CREATE TABLE IF NOT EXISTS won't touch existing data.
# ALTER TABLE is wrapped in try/except so missing columns get added safely.
init_db()

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/otp")
def otp():
    return render_template("otp.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
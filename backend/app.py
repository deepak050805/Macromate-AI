from flask import Flask
from flask_cors import CORS
from models import init_db
from routes.macros import macros_bp
from routes.auth import auth_bp
from routes.tracker import tracker_bp

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "secret123"

app.register_blueprint(macros_bp, url_prefix="/api/macros")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(tracker_bp, url_prefix="/api/tracker")

# Initialize DB on every startup — safe to run repeatedly
# CREATE TABLE IF NOT EXISTS won't touch existing data
# ALTER TABLE is wrapped in try/except so missing columns get added safely
init_db()

@app.route("/")
def home():
    return {"message": "MacroMate API Running 🚀"}

if __name__ == "__main__":
    app.run(debug=True)
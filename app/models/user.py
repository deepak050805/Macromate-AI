"""User schema retains legacy column names for a safe migration."""
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    is_verified = db.Column(db.Integer, nullable=False, default=0)
    role = db.Column(db.Text, nullable=False, default="user")
    auth_version = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

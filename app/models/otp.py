from app.extensions import db


class Otp(db.Model):
    __tablename__ = "otp_challenges"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    digest = db.Column(db.String(64), nullable=False)
    purpose = db.Column(db.String(12), nullable=False)
    expires_at = db.Column(db.Float, nullable=False)
    sent_at = db.Column(db.Float, nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)

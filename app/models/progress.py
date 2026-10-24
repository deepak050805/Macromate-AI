from app.extensions import db


class Progress(db.Model):
    __tablename__ = "progress"
    __table_args__ = (
        db.CheckConstraint("weight > 0 AND weight <= 500", name="ck_progress_weight"),
        db.CheckConstraint("calories >= 0 AND calories <= 20000", name="ck_progress_calories"),
        db.Index("ix_progress_email_date", "email", "record_date", "id"),
    )
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, db.ForeignKey("users.email"), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    record_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    def as_dict(self):
        return {"id": self.id, "weight": self.weight, "calories": self.calories,
                "date": self.record_date.isoformat() if self.record_date else None}

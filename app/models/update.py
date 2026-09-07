"""
app/models/update.py — Daily Update Model
"""
from datetime import datetime
from app.extensions import db


class DailyUpdate(db.Model):
    """
    A daily update posted by the MENTOR_ADMIN.
    Can be course-specific or global (course_id=None).
    
    Example: "Today: Watch Flask video, complete quiz, practice 5 problems."
    """
    __tablename__ = 'daily_updates'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    # ^ If set: only students in this course see this update.
    # ^ If None: shown to all students (global update).

    is_pinned = db.Column(db.Boolean, default=False)
    # ^ Pinned updates always show at the top.

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # Relationships
    course = db.relationship('Course', back_populates='daily_updates')

    def __repr__(self):
        return f'<DailyUpdate {self.title}>'

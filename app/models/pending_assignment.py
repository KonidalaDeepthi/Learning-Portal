"""Pending email-based course assignments."""
from datetime import datetime

from app.extensions import db


class PendingCourseAssignment(db.Model):
    """Course access assigned before a student creates an account."""

    __tablename__ = 'pending_course_assignments'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    course = db.relationship('Course')
    assigner = db.relationship(
        'User',
        foreign_keys=[assigned_by],
        back_populates='pending_course_assignments'
    )

    __table_args__ = (
        db.Index(
            'uq_pending_active_email_course',
            'email', 'course_id',
            unique=True,
            sqlite_where=db.text('is_active = 1'),
            postgresql_where=db.text('is_active = true'),
        ),
    )

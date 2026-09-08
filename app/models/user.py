"""
app/models/user.py — User Model
=================================
This model represents every person in the system:
both STUDENTS and the MENTOR_ADMIN.

KEY CONCEPTS:
- db.Model: Makes this class a database table
- db.Column: Defines each column in the table
- UserMixin: Gives Flask-Login the methods it needs
  (is_authenticated, is_active, get_id, etc.)
"""

from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    """
    Represents a user in the system.
    
    role = 'STUDENT'      → Normal student
    role = 'MENTOR_ADMIN' → Full platform control & Student Portal access
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True, default='EMAIL_ONLY_AUTH')  # Legacy optional column
    role = db.Column(db.String(20), nullable=False, default='STUDENT')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    theme_preference = db.Column(db.String(10), default='light', nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # ----------------------------------------------------------
    # Relationships
    # ----------------------------------------------------------
    enrollments = db.relationship('CourseEnrollment', back_populates='user',
                                  lazy='dynamic', cascade='all, delete-orphan')

    quiz_attempts = db.relationship('QuizAttempt', back_populates='user',
                                    lazy='dynamic', cascade='all, delete-orphan')

    student_conversations = db.relationship(
        'Conversation',
        foreign_keys='Conversation.student_id',
        back_populates='student',
        lazy='dynamic'
    )

    notifications = db.relationship('Notification', back_populates='user',
                                    lazy='dynamic', cascade='all, delete-orphan')

    pending_course_assignments = db.relationship(
        'PendingCourseAssignment',
        foreign_keys='PendingCourseAssignment.assigned_by',
        back_populates='assigner',
        lazy='dynamic'
    )

    # ----------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------

    @property
    def is_mentor_admin(self):
        """Quick check: is this user the Mentor/Admin?"""
        return self.role is not None and self.role.upper() == 'MENTOR_ADMIN'

    @property
    def is_student(self):
        """Quick check: is this user a student?"""
        return self.role is not None and self.role.upper() == 'STUDENT'

    def get_enrolled_courses(self):
        """Return all active courses this user is enrolled in."""
        return [e.course for e in self.enrollments if e.is_active and e.course.status == 'active']

    def is_enrolled_in(self, course_id):
        """Check if this user is actively enrolled in a specific course."""
        enrollment = self.enrollments.filter_by(
            course_id=course_id,
            is_active=True
        ).first()
        return enrollment is not None

    def get_unread_notification_count(self):
        """Count unread notifications for the notification bell."""
        return self.notifications.filter_by(is_read=False).count()

    def get_unread_message_notification_count(self):
        """Count unread private-chat notifications for the message badge."""
        return self.notifications.filter_by(
            type='message',
            is_read=False
        ).count()

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


# ----------------------------------------------------------
# User Loader
# ----------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login session management."""
    return User.query.get(int(user_id))


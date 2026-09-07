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
    
    role = 'student'      → Normal student
    role = 'mentor_admin' → Full platform control (you)
    """

    __tablename__ = 'users'

    # ----------------------------------------------------------
    # Columns
    # ----------------------------------------------------------

    id = db.Column(db.Integer, primary_key=True)
    # ^ Every row gets a unique number automatically

    name = db.Column(db.String(100), nullable=False)
    # ^ Full name, required (nullable=False means it can't be empty)

    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    # ^ Email must be unique across all users. index=True makes searches fast.

    password_hash = db.Column(db.String(256), nullable=False)
    # ^ We NEVER store the actual password. Only this hashed version.

    role = db.Column(db.String(20), nullable=False, default='student')
    # ^ 'student' or 'mentor_admin'. Default is always 'student'.

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # ^ If False, the user cannot log in even with correct password.

    theme_preference = db.Column(db.String(10), default='light', nullable=False)
    # ^ 'light' or 'dark'. Saves the user's preferred theme.

    profile_picture = db.Column(db.String(200), nullable=True)
    # ^ Optional URL to a profile picture.

    last_login = db.Column(db.DateTime, nullable=True)
    # ^ Tracks when the user last logged in. Useful for mentor monitoring.

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # ^ Automatically set to current time when user is created.

    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)
    # ^ Automatically updated whenever the row is modified.

    # ----------------------------------------------------------
    # Relationships
    # These tell SQLAlchemy how tables connect to each other.
    # 'lazy=True' means data is only fetched when you actually need it.
    # ----------------------------------------------------------

    # One user can have many course enrollments
    enrollments = db.relationship('CourseEnrollment', back_populates='user',
                                  lazy='dynamic', cascade='all, delete-orphan')

    # One user can have many quiz attempts
    quiz_attempts = db.relationship('QuizAttempt', back_populates='user',
                                    lazy='dynamic', cascade='all, delete-orphan')

    # Student's conversations with the mentor
    student_conversations = db.relationship(
        'Conversation',
        foreign_keys='Conversation.student_id',
        back_populates='student',
        lazy='dynamic'
    )

    # Notifications for this user
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
        return self.role == 'mentor_admin'

    @property
    def is_student(self):
        """Quick check: is this user a student?"""
        return self.role == 'student'

    def get_enrolled_courses(self):
        """Return all active courses this student is enrolled in."""
        return [e.course for e in self.enrollments if e.is_active and e.course.status == 'active']

    def is_enrolled_in(self, course_id):
        """Check if this student is actively enrolled in a specific course."""
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
        """How this object appears when printed for debugging."""
        return f'<User {self.email} ({self.role})>'


# ----------------------------------------------------------
# User Loader
# Flask-Login calls this function to get the current user
# from their session. It uses the user's ID stored in the cookie.
# ----------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login session management."""
    return User.query.get(int(user_id))

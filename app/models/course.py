"""
app/models/course.py — Course and Enrollment Models
=====================================================
Two models in this file:

1. Course — represents a course (Python Full Stack, Generative AI, etc.)
2. CourseEnrollment — links a student to a course

WHY TWO TABLES?
A student can belong to many courses.
A course can contain many students.
This is a Many-to-Many relationship.
We use CourseEnrollment as the "join table" that sits in between,
which also lets us store extra info like 'assigned_at' and 'is_active'.
"""

from datetime import datetime
from app.extensions import db


class Course(db.Model):
    """
    Represents a learning course on the platform.
    
    Examples:
    - Python Full Stack
    - Generative AI
    - (Future: DSA, Java, Data Science...)
    
    The architecture is fully generic — new courses can be added
    from the Mentor Dashboard without any code changes.
    """

    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), unique=True, nullable=False)
    # ^ Course name must be unique. e.g. "Python Full Stack"

    description = db.Column(db.Text, nullable=True)
    # ^ Optional longer description of the course

    status = db.Column(db.String(20), default='active', nullable=False)
    # ^ 'active' or 'inactive'. Inactive courses are hidden from students.

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # ^ Which user created this course (always MENTOR_ADMIN)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # ----------------------------------------------------------
    # Relationships — one course has many of these
    # ----------------------------------------------------------
    enrollments = db.relationship('CourseEnrollment', back_populates='course',
                                  lazy='dynamic', cascade='all, delete-orphan')

    videos = db.relationship('Video', back_populates='course',
                             lazy='dynamic', cascade='all, delete-orphan')

    quizzes = db.relationship('Quiz', back_populates='course',
                              lazy='dynamic', cascade='all, delete-orphan')

    daily_updates = db.relationship('DailyUpdate', back_populates='course',
                                    lazy='dynamic', cascade='all, delete-orphan')

    announcements = db.relationship('Announcement', back_populates='target_course',
                                    lazy='dynamic')

    # ----------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------

    def get_active_students(self):
        """Return all students actively enrolled in this course."""
        return [e.user for e in self.enrollments.filter_by(is_active=True).all()]

    def get_student_count(self):
        """Count active students in this course."""
        return self.enrollments.filter_by(is_active=True).count()

    def get_published_quizzes(self):
        """Return only published quizzes for student view."""
        return self.quizzes.filter_by(status='published').all()

    def get_published_videos(self):
        """Return only published videos for student view."""
        return self.videos.filter_by(status='published').all()

    def __repr__(self):
        return f'<Course {self.name}>'


class CourseEnrollment(db.Model):
    """
    Links a Student (User) to a Course.
    
    This is the Many-to-Many join table.
    
    Example rows:
    user_id=5, course_id=1 → Rahul is enrolled in Python Full Stack
    user_id=5, course_id=2 → Rahul is also enrolled in Generative AI
    user_id=6, course_id=1 → Priya is only in Python Full Stack
    """

    __tablename__ = 'course_enrollments'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # ^ Which student

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    # ^ Which course

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # ^ MENTOR_ADMIN can deactivate access without deleting the record.
    # This means the history is preserved.

    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # ^ When the student was assigned to this course

    # Unique constraint: a student can only be in a course ONCE
    # This prevents accidental duplicates
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='uq_user_course'),
    )

    # ----------------------------------------------------------
    # Relationships
    # ----------------------------------------------------------
    user = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

    def __repr__(self):
        return f'<Enrollment user={self.user_id} course={self.course_id} active={self.is_active}>'

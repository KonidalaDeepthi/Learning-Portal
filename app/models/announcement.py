"""
app/models/announcement.py — Announcement and Notification Models
"""
from datetime import datetime
from app.extensions import db


class Announcement(db.Model):
    """
    A message from the MENTOR_ADMIN to a group of students.
    Can target: all students, or students in a specific course.
    """
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    target_type = db.Column(db.String(20), nullable=False, default='all')
    # ^ 'all' = every student. 'course' = only students in target_course_id.

    target_course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    # ^ Only set if target_type == 'course'

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    target_course = db.relationship('Course', back_populates='announcements')

    def __repr__(self):
        return f'<Announcement {self.title} → {self.target_type}>'


class Notification(db.Model):
    """
    An in-app notification for a specific student.
    Created automatically when:
    - A new quiz is published
    - A new video is added
    - A new daily update is posted
    - A new announcement targets the student
    - The mentor sends a message
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # ^ Which student receives this notification

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)

    type = db.Column(db.String(50), nullable=False)
    # ^ 'quiz', 'video', 'update', 'message', 'announcement'

    is_read = db.Column(db.Boolean, default=False, nullable=False)
    related_id = db.Column(db.Integer, nullable=True)
    # ^ ID of the related object (quiz_id, video_id, etc.) for linking

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.type} for user={self.user_id} read={self.is_read}>'

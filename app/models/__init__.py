"""
app/models/__init__.py
Imports all models so they are registered with SQLAlchemy.
This file must import every model so db.create_all() finds them.
"""

from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.models.pending_assignment import PendingCourseAssignment
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from app.models.video import Video
from app.models.update import DailyUpdate
from app.models.chat import Conversation, Message
from app.models.announcement import Announcement, Notification

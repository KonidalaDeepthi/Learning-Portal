"""Shared course-access operations for mentor assignment and registration."""
from datetime import datetime

from app.extensions import db
from app.models.course import CourseEnrollment
from app.models.pending_assignment import PendingCourseAssignment
from app.models.user import User


def normalize_email(email):
    """Return the canonical email form used by account and assignment queries."""
    return (email or '').strip().lower()


def assign_course_by_email(email, course, assigned_by):
    """Assign or queue course access without creating or elevating users."""
    normalized_email = normalize_email(email)
    student = User.query.filter_by(email=normalized_email).first()

    if student and student.role != 'student':
        return 'not_student', student

    if student:
        enrollment = CourseEnrollment.query.filter_by(
            user_id=student.id,
            course_id=course.id
        ).first()
        if enrollment is None:
            db.session.add(CourseEnrollment(
                user_id=student.id,
                course_id=course.id
            ))
        else:
            enrollment.is_active = True

        PendingCourseAssignment.query.filter_by(
            email=normalized_email,
            course_id=course.id,
            is_active=True
        ).update({'is_active': False}, synchronize_session=False)
        return 'enrolled', student

    pending = PendingCourseAssignment.query.filter_by(
        email=normalized_email,
        course_id=course.id,
        is_active=True
    ).first()
    if pending is None:
        db.session.add(PendingCourseAssignment(
            email=normalized_email,
            course_id=course.id,
            assigned_by=assigned_by,
            assigned_at=datetime.utcnow(),
            is_active=True
        ))
    return 'pending', None


def fulfill_pending_assignments(student):
    """Enroll a newly registered student in all active pending assignments."""
    pending_assignments = PendingCourseAssignment.query.filter_by(
        email=normalize_email(student.email),
        is_active=True
    ).all()
    for pending in pending_assignments:
        enrollment = CourseEnrollment.query.filter_by(
            user_id=student.id,
            course_id=pending.course_id
        ).first()
        if enrollment is None:
            db.session.add(CourseEnrollment(
                user_id=student.id,
                course_id=pending.course_id
            ))
        else:
            enrollment.is_active = True
        pending.is_active = False
    return pending_assignments

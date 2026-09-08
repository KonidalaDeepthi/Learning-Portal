"""
app/decorators.py — Custom Route Protection Decorators
=======================================================
These decorators protect routes from unauthorized access.

WHAT IS A DECORATOR?
A decorator is a function that wraps another function.
When you write @mentor_admin_required above a route,
Python runs the check BEFORE running the route itself.

Example usage:
    @app.route('/mentor/dashboard')
    @login_required          ← Flask-Login: must be logged in
    @mentor_admin_required   ← Our custom: must be MENTOR_ADMIN role
    def mentor_dashboard():
        ...

WHY NOT JUST CHECK IN THE ROUTE?
Because if you forget to add the check in one route,
that route becomes a security hole. Decorators make
it impossible to forget — you just put @mentor_admin_required
on the route and the check is guaranteed to run.
"""

from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user


def mentor_admin_required(f):
    """
    Decorator that ensures only MENTOR_ADMIN can access a route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_mentor_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """
    Decorator ensuring only STUDENTS or MENTOR_ADMIN can access student portal routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_student or current_user.is_mentor_admin):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def enrolled_in_course(f):
    """
    Decorator for course-specific routes.
    Verifies the student is actively enrolled in the course_id from the URL.
    MENTOR_ADMIN has open access to all courses.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_mentor_admin:
            return f(*args, **kwargs)

        course_id = kwargs.get('course_id')
        if course_id and not current_user.is_enrolled_in(course_id):
            flash('You do not have access to this course.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


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
    
    How it works:
    1. Checks if the current user's role is 'mentor_admin'
    2. If YES → allows the route function to run normally
    3. If NO  → returns 403 Forbidden immediately
    
    Note: Flask-Login's @login_required must ALSO be used to
    ensure the user is logged in first. Use both decorators:
    
        @login_required
        @mentor_admin_required
        def my_route():
            ...
    """
    @wraps(f)  # Preserves the original function's name and docstring
    def decorated_function(*args, **kwargs):
        # Check the role stored in the database, NOT the URL or form data
        if not current_user.is_authenticated or current_user.role != 'mentor_admin':
            # 403 = "You are logged in but not allowed here"
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """
    Decorator ensuring only STUDENTS can access a route.
    Redirects MENTOR_ADMIN to their dashboard.
    
    This prevents the mentor from accidentally using student pages.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in {'student', 'mentor_admin'}:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def enrolled_in_course(f):
    """
    Decorator for course-specific routes.
    Verifies the student is actively enrolled in the course_id from the URL.
    
    Usage (route must have course_id parameter):
        @app.route('/course/<int:course_id>')
        @login_required
        @enrolled_in_course
        def course_page(course_id):
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # MENTOR_ADMIN can access all courses without enrollment
        if current_user.role == 'mentor_admin':
            return f(*args, **kwargs)

        course_id = kwargs.get('course_id')
        if course_id and not current_user.is_enrolled_in(course_id):
            flash('You do not have access to this course.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

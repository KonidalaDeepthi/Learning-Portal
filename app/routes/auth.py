"""
app/routes/auth.py — Authentication Routes
===========================================
Handles: Login, Register, Logout

BLUEPRINT: auth_bp
All routes here are prefixed with nothing extra,
so /login, /register, /logout are the final URLs.

HOW BLUEPRINTS WORK:
A Blueprint is like a mini Flask app for a group of routes.
We define routes here, then register the blueprint in __init__.py.
This keeps the code organised — auth routes stay in auth.py,
student routes in student.py, etc.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from app.extensions import db
from app.models.user import User
from app.course_access import normalize_email

# Create the Blueprint
# 'auth' is the name used in url_for('auth.login') etc.
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  /login → Show the login form
    POST /login → Process the submitted email ID
    """
    # If user is already logged in, redirect to correct dashboard
    if current_user.is_authenticated:
        return _redirect_after_login(current_user)

    if request.method == 'POST':
        email = normalize_email(request.form.get('email', ''))
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/login.html')

        # --- Find user in database by normalized email ---
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('This email is not registered. Please contact your Mentor/Admin.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
            return render_template('auth/login.html')

        # --- All checks passed — log the user in using their actual User.id ---
        login_user(user)

        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.session.commit()

        flash(f'Welcome back, {user.name}! 👋', 'success')

        # Redirect to the page they originally tried to access (if any)
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)

        return _redirect_after_login(user)

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Public self-registration is disabled; Mentor/Admin creates students."""
    abort(404)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ----------------------------------------------------------
# Helper function
# ----------------------------------------------------------
def _redirect_after_login(user):
    """Redirect user to the correct portal based on their role."""
    if user.is_mentor_admin:
        return redirect(url_for('mentor.dashboard'))
    else:
        return redirect(url_for('student.home'))


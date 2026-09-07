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

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app.extensions import db
from app.models.user import User
from app.course_access import fulfill_pending_assignments, normalize_email

# Create the Blueprint
# 'auth' is the name used in url_for('auth.login') etc.
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  /login → Show the login form
    POST /login → Process the submitted email + password
    """
    # If user is already logged in, redirect to correct dashboard
    if current_user.is_authenticated:
        return _redirect_after_login(current_user)

    if request.method == 'POST':
        email = normalize_email(request.form.get('email', ''))
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        # --- Validation ---
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html')

        # --- Find user in database ---
        user = User.query.filter_by(email=email).first()

        # --- Security checks (deliberate vague message to attackers) ---
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
            return render_template('auth/login.html')

        # --- All checks passed — log the user in ---
        login_user(user, remember=bool(remember))

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
    """
    GET  /register → Show registration form
    POST /register → Create a new STUDENT account

    IMPORTANT: This ALWAYS creates a STUDENT account.
    The MENTOR_ADMIN account is created via 'flask seed-admin'.
    """
    # Already logged in? Redirect appropriately.
    if current_user.is_authenticated:
        return _redirect_after_login(current_user)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = normalize_email(request.form.get('email', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # --- Validation ---
        errors = []

        if not name or len(name) < 2:
            errors.append('Please enter your full name (at least 2 characters).')

        if not email or '@' not in email or ' ' in email:
            errors.append('Please enter a valid email address.')

        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters long.')

        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html',
                                   name=name, email=email)

        # --- Check if email already exists ---
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('This email is already registered. Please log in instead.', 'warning')
            return render_template('auth/register.html',
                                   name=name, email=email)

        # --- Create the student account ---
        # ALWAYS role='student' — hardcoded, cannot be changed by user input
        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role='student',        # ← ALWAYS student from registration
            is_active=True,
            theme_preference='light'
        )

        db.session.add(new_user)
        db.session.flush()
        fulfill_pending_assignments(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Logs the user out:
    1. Clears Flask-Login session
    2. Clears Flask session data
    3. Redirects to login page

    After logout, browser Back button should NOT show protected content
    because the server will check the session on every request.
    """
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


# ----------------------------------------------------------
# Helper function
# ----------------------------------------------------------
def _redirect_after_login(user):
    """Redirect user to the correct dashboard based on their role."""
    if user.role == 'mentor_admin':
        return redirect(url_for('mentor.dashboard'))
    else:
        return redirect(url_for('student.home'))

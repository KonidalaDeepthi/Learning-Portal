"""
app/extensions.py — Flask Extensions
======================================
This file creates the extension objects (db, login_manager, csrf)
WITHOUT attaching them to any app yet.

WHY DO WE DO THIS?
We use the "Application Factory" pattern. This means we create
Flask extensions here as empty objects, and later in __init__.py
we attach them to the real app using init_app(app).

This pattern makes the app easier to test and configure.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Database object — used in every model with db.Model, db.Column etc.
db = SQLAlchemy()

# Login manager — handles "is user logged in?" for every route
login_manager = LoginManager()

# CSRF protection — automatically adds security tokens to all forms
csrf = CSRFProtect()

# Configure what happens when a non-logged-in user hits a protected page
# It redirects them to the 'auth.login' route (our login page)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

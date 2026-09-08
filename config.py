"""
config.py — Application Configuration
======================================
This file reads values from the .env file and makes them
available to the Flask app in a clean, organised way.

Think of this as the "settings" file for the entire application.
"""

import os
from dotenv import load_dotenv

# Load the .env file so we can read its values
load_dotenv()


class Config:
    """
    Base configuration class.
    All settings are read from environment variables (.env file).
    """

    # ----------------------------------------------------------
    # SECRET KEY
    # Flask uses this to sign session cookies securely.
    # If someone knows this key, they can forge sessions.
    # ALWAYS keep this secret and long.
    # ----------------------------------------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-dev-key-change-in-production'

    # ----------------------------------------------------------
    # DATABASE
    # SQLAlchemy reads this URI to know which database to use.
    # sqlite:///app.db means a file called app.db in the
    # instance/ folder (Flask creates this folder automatically).
    # ----------------------------------------------------------
    _database_url = os.environ.get('DATABASE_URL')
    if _database_url and _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _database_url or 'sqlite:///app.db'

    # This turns off a SQLAlchemy feature we don't need.
    # Saves memory and removes an annoying warning.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ----------------------------------------------------------
    # WTF (Flask-WTF) — CSRF Protection
    # CSRF = Cross-Site Request Forgery. This setting ensures
    # Flask-WTF generates security tokens for all forms.
    # ----------------------------------------------------------
    WTF_CSRF_ENABLED = True

    # ----------------------------------------------------------
    # MENTOR_ADMIN Credentials (read from .env)
    # These are used ONLY by the seed command to create the
    # admin account. They are never shown to users.
    # ----------------------------------------------------------
    MENTOR_ADMIN_EMAIL = os.environ.get('MENTOR_ADMIN_EMAIL')
    MENTOR_ADMIN_NAME = os.environ.get('MENTOR_ADMIN_NAME')

    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL') or 'neoskillzinfo@gmail.com'


class DevelopmentConfig(Config):
    """Development settings — shows debug errors in browser."""
    DEBUG = True


class ProductionConfig(Config):
    """Production settings — hides errors, maximises security."""
    DEBUG = False


# Dictionary so we can select config by name
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

"""
app.py — Application Entry Point
==================================
This is the file you run to start the server.

It creates the app using the factory, and also registers
custom Flask CLI commands like 'flask seed-admin'.

HOW TO RUN:
    python app.py
    OR
    flask run
"""

import os

from app import create_app
from app.extensions import db

# Use production configuration when the hosting environment requests it.
app = create_app(os.environ.get('FLASK_CONFIG', 'development'))


# ============================================================
# CLI COMMAND: flask seed-admin
# ============================================================
# Run this ONCE after setting up the project to create:
# 1. The MENTOR_ADMIN account (from .env credentials)
# 2. The two initial courses: Python Full Stack, Generative AI
# ============================================================
@app.cli.command('seed-admin')
def seed_admin():
    """
    Create the MENTOR_ADMIN account and seed initial courses.
    Run this command once: flask seed-admin
    """
    from app.models.user import User
    from app.models.course import Course
    import os

    print("\n========================================")
    print("   Mentor Platform — Initial Setup")
    print("========================================\n")


    # --- Create MENTOR_ADMIN ---
    admin_email = app.config.get('MENTOR_ADMIN_EMAIL')
    admin_name = app.config.get('MENTOR_ADMIN_NAME')

    if not all([admin_email, admin_name]):
        print("❌ ERROR: MENTOR_ADMIN_EMAIL and MENTOR_ADMIN_NAME must be set in your .env file.")
        return

    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        existing_admin.role = 'mentor_admin'
        existing_admin.is_active = True
        db.session.commit()
        print(f"✓ MENTOR_ADMIN already exists: {admin_email}")
    else:
        admin = User(
            name=admin_name,
            email=admin_email,
            role='mentor_admin',
            is_active=True,
            theme_preference='dark'
        )
        db.session.add(admin)
        print(f"✓ Created MENTOR_ADMIN: {admin_email}")

    # --- Seed Initial Courses ---
    courses = [
        {
            'name': 'Python Full Stack',
            'status': 'active'
        },
        {
            'name': 'Generative AI',
            'description': 'Explore Generative AI concepts, large language models, prompt engineering, APIs, and building AI-powered applications.',
            'status': 'active'
        }
    ]

    admin_user = User.query.filter_by(email=admin_email).first()

    for course_data in courses:
        existing = Course.query.filter_by(name=course_data['name']).first()
        if existing:
            print(f"✓ Course already exists: {course_data['name']}")
        else:
            # We need the admin user's ID — commit admin first if new
            db.session.flush()
            admin_user = User.query.filter_by(email=admin_email).first()
            course = Course(
                name=course_data['name'],
                description=course_data.get('description', ''),
                status=course_data['status'],
                created_by=admin_user.id if admin_user else None
            )
            db.session.add(course)
            print(f"✓ Created course: {course_data['name']}")

    db.session.commit()

    print("\n========================================")
    print("   Setup complete!")
    print(f"   Login at: /login")
    print(f"   Admin email: {admin_email}")
    print("   (Password is in your .env file)")
    print("========================================\n")

if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', False))

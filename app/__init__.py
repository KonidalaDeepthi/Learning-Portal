"""
app/__init__.py — Application Factory
=======================================
This is the heart of the Flask application.

The create_app() function:
1. Creates a Flask app object
2. Loads configuration from config.py
3. Initialises all extensions (db, login, csrf)
4. Registers all Blueprints (route groups)
5. Creates the database tables if they don't exist
6. Returns the ready app

WHY USE A FACTORY FUNCTION?
Instead of creating the app at module level (app = Flask(__name__)),
we wrap it in a function. This lets us create different versions
of the app for testing, development, and production.
"""

from flask import Flask, redirect, url_for
from config import config
from app.extensions import db, login_manager, csrf
from sqlalchemy import inspect, text


def create_app(config_name='default'):
    """
    Application factory function.
    Call this to get a fully configured Flask app.
    """

    # Create the Flask app
    # __name__ tells Flask where to find templates and static files
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from config.py
    app.config.from_object(config[config_name])

    # ----------------------------------------------------------
    # Initialise extensions
    # Now we connect the empty extension objects to our real app
    # ----------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ----------------------------------------------------------
    # Register Blueprints (route groups)
    # Each Blueprint handles one section of the site.
    # ----------------------------------------------------------
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.student import student_bp
    app.register_blueprint(student_bp)

    from app.routes.mentor import mentor_bp
    app.register_blueprint(mentor_bp)

    # Register all models so db.create_all() finds them
    from app.models import user, course, quiz, video, update, chat, announcement  # noqa: F401

    # ----------------------------------------------------------
    # Root route — redirect to login
    # When someone opens the website, always show login first.
    # ----------------------------------------------------------
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # ----------------------------------------------------------
    # Theme API — saves theme preference to DB
    # Called by theme.js when user toggles light/dark mode.
    # ----------------------------------------------------------
    @app.route('/api/set-theme', methods=['POST'])
    def set_theme():
        from flask import request, jsonify
        from flask_login import current_user
        if current_user.is_authenticated:
            data = request.get_json()
            theme = data.get('theme', 'light')
            if theme in ['light', 'dark']:
                current_user.theme_preference = theme
                db.session.commit()
        return jsonify({'status': 'ok'})

    @app.context_processor
    def mentor_shell_context():
        from flask_login import current_user
        if not current_user.is_authenticated or current_user.role != 'mentor_admin':
            return {}
        from app.models.announcement import Notification
        unread_messages = Notification.query.filter_by(
            user_id=current_user.id,
            type='message',
            is_read=False
        ).count()
        return {'mentor_unread_messages': unread_messages}

    # ----------------------------------------------------------
    # Custom error pages
    # ----------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    # ----------------------------------------------------------
    # Create all database tables
    # This reads all model classes and creates their tables
    # in the database if they don't exist yet.
    # ----------------------------------------------------------
    with app.app_context():
        inspector = inspect(db.engine)
        if 'videos' in inspector.get_table_names():
            video_columns = {column['name'] for column in inspector.get_columns('videos')}
            if 'day_number' not in video_columns:
                with db.engine.begin() as connection:
                    connection.execute(text('ALTER TABLE videos ADD COLUMN day_number INTEGER'))
        if 'quizzes' in inspector.get_table_names():
            quiz_columns = {column['name'] for column in inspector.get_columns('quizzes')}
            question_columns = {column['name'] for column in inspector.get_columns('quiz_questions')}
            with db.engine.begin() as connection:
                if 'day_number' not in quiz_columns:
                    connection.execute(text('ALTER TABLE quizzes ADD COLUMN day_number INTEGER'))
                if 'explanation' not in question_columns:
                    connection.execute(text("ALTER TABLE quiz_questions ADD COLUMN explanation TEXT NOT NULL DEFAULT ''"))
        if 'quiz_answers' in inspector.get_table_names():
            answer_columns = {column['name'] for column in inspector.get_columns('quiz_answers')}
            if 'answered_at' not in answer_columns:
                with db.engine.begin() as connection:
                    connection.execute(text("ALTER TABLE quiz_answers ADD COLUMN answered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))
        if 'conversations' in inspector.get_table_names():
            conversation_columns = {column['name'] for column in inspector.get_columns('conversations')}
            if 'course_id' not in conversation_columns:
                with db.engine.begin() as connection:
                    connection.execute(text('ALTER TABLE conversations ADD COLUMN course_id INTEGER REFERENCES courses(id)'))
        if 'quiz_attempts' in inspector.get_table_names() and db.engine.dialect.name == 'sqlite':
            constraints = inspector.get_unique_constraints('quiz_attempts')
            if any(constraint.get('name') == 'uq_user_quiz_attempt' for constraint in constraints):
                with db.engine.begin() as connection:
                    connection.execute(text('PRAGMA foreign_keys=OFF'))
                    connection.execute(text('''
                        CREATE TABLE quiz_attempts_migrated (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            quiz_id INTEGER NOT NULL,
                            score INTEGER NOT NULL DEFAULT 0,
                            total_marks INTEGER NOT NULL DEFAULT 0,
                            percentage FLOAT NOT NULL DEFAULT 0.0,
                            correct_count INTEGER NOT NULL DEFAULT 0,
                            wrong_count INTEGER NOT NULL DEFAULT 0,
                            skipped_count INTEGER NOT NULL DEFAULT 0,
                            started_at DATETIME NOT NULL,
                            submitted_at DATETIME,
                            FOREIGN KEY(user_id) REFERENCES users(id),
                            FOREIGN KEY(quiz_id) REFERENCES quizzes(id)
                        )
                    '''))
                    connection.execute(text('''
                        INSERT INTO quiz_attempts_migrated
                        SELECT id, user_id, quiz_id, score, total_marks, percentage,
                               correct_count, wrong_count, skipped_count, started_at,
                               submitted_at
                        FROM quiz_attempts
                    '''))
                    connection.execute(text('DROP TABLE quiz_attempts'))
                    connection.execute(text('ALTER TABLE quiz_attempts_migrated RENAME TO quiz_attempts'))
                    connection.execute(text('PRAGMA foreign_keys=ON'))
        db.create_all()

    @app.cli.command('seed-videos')
    def seed_videos():
        """Replace all existing videos with the initial Python curriculum."""
        from app.models.course import Course
        from app.models.user import User
        from app.models.video import Video

        urls = [
            'https://youtu.be/WvVtZuVMKXw', 'https://youtu.be/xFV5HhMwDJA',
            'https://youtu.be/IJWmTBCFkjM', 'https://youtu.be/LS3LM92s_rw',
            'https://youtu.be/bboHKtZmXLs', 'https://youtu.be/OW_3hWLrPNI',
            'https://youtu.be/krbnNLO-W4M', 'https://youtu.be/FowBRHec2eU',
            'https://youtu.be/hvwiAIFqmYM', 'https://youtu.be/odLUOqf8GXQ',
            'https://youtu.be/j13M0mjD65Y', 'https://youtu.be/YNxrrfPafvg',
        ]
        titles = [
            'Introduction to Python',
            'Comments, Variables, Data Types & Type Testing',
            'Control Statements & Looping Statements',
            'Lists',
            'Strings',
            'Dictionaries & Tuples',
            'Sets',
            'Functions & Advanced Functions',
            'Mock Interview',
            'File Handling & Error Handling',
            'OOPs Part 1',
            'OOPs Part 2',
        ]
        course = Course.query.filter_by(name='Python Full Stack').first()
        if not course:
            raise RuntimeError('Python Full Stack course does not exist.')
        mentor = User.query.filter_by(role='mentor_admin').first()
        Video.query.delete()
        for day_number, (url, title) in enumerate(zip(urls, titles), start=1):
            db.session.add(Video(
            title=title, description='', url=url,
                course_id=course.id, day_number=day_number,
                order_index=day_number, resource_type='video',
                status='published', created_by=mentor.id if mentor else None,
            ))
        db.session.commit()
        print('Replaced all videos with 12 Python Full Stack videos.')

    @app.cli.command('seed-quizzes')
    def seed_quizzes():
        """Replace Python Full Stack quiz content with the 12-topic curriculum."""
        from app.quiz_seed import seed_python_full_stack_quizzes
        seed_python_full_stack_quizzes()
        print('Seeded 12 Python Full Stack quizzes with 360 questions.')

    @app.cli.command('seed-generative-ai-recordings')
    def seed_generative_ai_recordings():
        """Replace Generative AI recordings with the supplied Day 1-Day 41 URLs."""
        from app.recording_seed import seed_generative_ai_recordings as seed_recordings
        seed_recordings()
        print('Seeded 41 Generative AI recordings. Day 42 was not created.')

    @app.cli.command('seed-generative-ai-quizzes')
    def seed_generative_ai_quizzes():
        """Create or repair the 15 Generative AI quizzes with 450 questions."""
        from app.generative_quiz_seed import seed_generative_ai_quizzes as seed_quizzes
        seed_quizzes()
        print('Seeded 15 Generative AI quizzes with 450 questions.')

    @app.cli.command('configure-mentor-admin')
    def configure_mentor_admin():
        """Create or repair only the configured Mentor/Admin account."""
        from werkzeug.security import generate_password_hash
        from app.models.user import User
        from app.models.course import Course, CourseEnrollment

        email = app.config.get('MENTOR_ADMIN_EMAIL')
        password = app.config.get('MENTOR_ADMIN_PASSWORD')
        name = app.config.get('MENTOR_ADMIN_NAME')
        if not all([email, password, name]):
            raise RuntimeError('MENTOR_ADMIN_EMAIL, MENTOR_ADMIN_PASSWORD, and MENTOR_ADMIN_NAME are required.')

        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(email=email, name=name)
            db.session.add(user)
        user.name = name
        user.password_hash = generate_password_hash(password)
        user.role = 'mentor_admin'
        user.is_active = True
        User.query.filter(
            User.role == 'mentor_admin',
            User.email != email
        ).update({'role': 'student'}, synchronize_session=False)
        for course in Course.query.filter_by(status='active').all():
            enrollment = CourseEnrollment.query.filter_by(
                user_id=user.id, course_id=course.id).first()
            if enrollment is None:
                db.session.add(CourseEnrollment(
                    user_id=user.id, course_id=course.id
                ))
            elif not enrollment.is_active:
                enrollment.is_active = True
        db.session.commit()
        print(f'Mentor/Admin configured for {email}; role=mentor_admin; active=True')

    @app.cli.command('configure-requested-enrollments')
    def configure_requested_enrollments():
        """Create normal student accounts and assign requested courses."""
        from secrets import token_urlsafe
        from werkzeug.security import generate_password_hash
        from app.models.user import User
        from app.models.course import Course, CourseEnrollment

        assignments = {
            'Python Full Stack': [
                'vahinilekkala@gmail.com', 'ssandhya49686@gmail.com',
                'likitha2006@gmail.com', 'chittoorpadmaja87@gmail.com',
                'jupallisahithya@gmail.com', 'chinthakayalajayanthi6@gmail.com',
                'madhavidasari908@gmail.com', 'nandhinianem200@gmail.com',
                'maddikayala953@gmail.com', 'rizimarizima2@gmail.com',
            ],
            'Generative AI': ['yasaswinigurijala1982@gmail.com'],
        }

        temporary_passwords = {}
        for course_name, emails in assignments.items():
            course = Course.query.filter_by(name=course_name).first()
            if not course:
                raise RuntimeError(f'Required course not found: {course_name}')

            for email in emails:
                user = User.query.filter_by(email=email).first()
                if user is None:
                    temporary_password = token_urlsafe(12)
                    user = User(
                        name=email.split('@', 1)[0].replace('.', ' ').title(),
                        email=email,
                        password_hash=generate_password_hash(temporary_password),
                        role='student', is_active=True, theme_preference='light',
                    )
                    db.session.add(user)
                    db.session.flush()
                    temporary_passwords[email] = temporary_password
                elif user.role != 'student':
                    raise RuntimeError(f'Refusing to change non-student account: {email}')

                enrollment = CourseEnrollment.query.filter_by(
                    user_id=user.id, course_id=course.id).first()
                if enrollment is None:
                    db.session.add(CourseEnrollment(user_id=user.id, course_id=course.id))
                else:
                    enrollment.is_active = True

        db.session.commit()
        print('Requested course enrollments configured successfully.')
        if temporary_passwords:
            print('Temporary passwords for newly created student accounts:')
            for email, password in temporary_passwords.items():
                print(f'  {email}: {password}')

    return app

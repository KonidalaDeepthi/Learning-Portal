import secrets

from werkzeug.security import check_password_hash

from app import create_app
from app.extensions import db
from app.models.course import Course, CourseEnrollment
from app.models.user import User


def test_mentor_created_student_authentication_and_course_access():
    app = create_app('development')
    app.config['WTF_CSRF_ENABLED'] = False
    suffix = secrets.token_hex(5)
    email = f'managed-{suffix}@example.com'
    password = secrets.token_urlsafe(16)

    with app.app_context():
        admin = User.query.filter_by(
            email=app.config['MENTOR_ADMIN_EMAIL']
        ).first()
        python_course = Course.query.filter_by(name='Python Full Stack').first()
        genai_course = Course.query.filter_by(name='Generative AI').first()
        assert admin is not None
        assert python_course is not None
        assert genai_course is not None
        python_course_id = python_course.id
        genai_course_id = genai_course.id

    client = app.test_client()
    assert client.post('/login', data={
        'email': app.config['MENTOR_ADMIN_EMAIL'],
        'password': app.config['MENTOR_ADMIN_PASSWORD'],
    }).status_code == 302

    response = client.post('/mentor/students/create', data={
        'name': 'Managed Student',
        'email': f'  {email.upper()}  ',
        'password': password,
        'course_id': python_course_id,
    })
    assert response.status_code == 302

    with app.app_context():
        student = User.query.filter_by(email=email).first()
        assert student is not None
        assert student.role == 'student'
        assert student.is_active is True
        assert student.password_hash != password
        assert check_password_hash(student.password_hash, password)
        assert CourseEnrollment.query.filter_by(
            user_id=student.id,
            course_id=python_course_id,
            is_active=True,
        ).count() == 1

    response = client.post('/mentor/students/create', data={
        'name': 'Managed Student Updated',
        'email': email.upper(),
        'password': secrets.token_urlsafe(16),
        'course_id': genai_course_id,
    })
    assert response.status_code == 302

    client.get('/logout')
    assert client.post('/login', data={
        'email': email.upper(),
        'password': password,
    }).status_code == 302
    courses_page = client.get('/courses').data.decode()
    assert f'/course/{python_course_id}' in courses_page
    assert f'/course/{genai_course_id}' in courses_page

    client.get('/logout')
    assert client.post('/login', data={
        'email': email,
        'password': password + 'wrong',
    }).status_code == 200

    with app.app_context():
        student = User.query.filter_by(email=email).first()
        db.session.delete(student)
        db.session.commit()


def test_public_registration_is_disabled():
    app = create_app('development')
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()
    assert client.get('/register').status_code == 404
    assert client.post('/register', data={
        'name': 'Public Student',
        'email': 'public@example.com',
        'password': secrets.token_urlsafe(12),
        'confirm_password': secrets.token_urlsafe(12),
    }).status_code == 404

import uuid

from flask_login import logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app
from app.extensions import db
from app.models.course import Course, CourseEnrollment
from app.models.pending_assignment import PendingCourseAssignment
from app.models.user import User


def test_pending_assignment_registration_and_authentication_flow():
    app = create_app('development')
    app.config['WTF_CSRF_ENABLED'] = False
    suffix = uuid.uuid4().hex[:10]
    pending_email = f'Pending-{suffix}@Example.com'
    both_email = f'both-{suffix}@example.com'
    existing_email = f'existing-{suffix}@example.com'
    inactive_email = f'inactive-{suffix}@example.com'
    password = 'Password123!'

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

        existing = User(
            name='Existing Student',
            email=existing_email,
            password_hash=generate_password_hash(password),
            role='student',
            is_active=True,
        )
        inactive = User(
            name='Inactive Student',
            email=inactive_email,
            password_hash=generate_password_hash(password),
            role='student',
            is_active=False,
        )
        db.session.add_all([existing, inactive])
        db.session.flush()
        db.session.add(CourseEnrollment(
            user_id=existing.id,
            course_id=python_course_id,
            is_active=False,
        ))
        db.session.commit()

    admin_client = app.test_client()
    assert admin_client.post('/login', data={
        'email': app.config['MENTOR_ADMIN_EMAIL'],
        'password': app.config['MENTOR_ADMIN_PASSWORD'],
    }).status_code == 302

    # A: assign before registration; duplicate assignment stays one row.
    for _ in range(2):
        response = admin_client.post('/mentor/students/assign-course', data={
            'email': f'  {pending_email}  ',
            'course_id': python_course_id,
        })
        assert response.status_code == 302

    # D/G: assign both courses before registration.
    for course_id in (python_course_id, genai_course_id):
        response = admin_client.post('/mentor/students/assign-course', data={
            'email': both_email.upper(),
            'course_id': course_id,
        })
        assert response.status_code == 302

    with app.app_context():
        assert PendingCourseAssignment.query.filter_by(
            email=pending_email.lower(), course_id=python_course_id, is_active=True
        ).count() == 1
        assert PendingCourseAssignment.query.filter_by(
            email=both_email.lower(), is_active=True
        ).count() == 2

    # H: existing student receives access immediately, without duplicates.
    response = admin_client.post('/mentor/students/assign-course', data={
        'email': existing_email.upper(),
        'course_id': python_course_id,
    })
    assert response.status_code == 302
    response = admin_client.post('/mentor/students/assign-course', data={
        'email': existing_email,
        'course_id': python_course_id,
    })
    assert response.status_code == 302

    with app.app_context():
        existing_user = User.query.filter_by(email=existing_email).first()
        assert CourseEnrollment.query.filter_by(
            user_id=existing_user.id,
            course_id=python_course_id,
            is_active=True,
        ).count() == 1

    existing_client = app.test_client()
    assert existing_client.post('/login', data={
        'email': existing_email,
        'password': password,
    }).status_code == 302
    assert b'Python Full Stack' in existing_client.get('/courses').data
    existing_client.get('/logout')

    # B/C: registration fulfills the pending Python assignment.
    pending_client = app.test_client()
    response = pending_client.post('/register', data={
        'name': 'Pending Student',
        'email': pending_email,
        'password': password,
        'confirm_password': password,
    })
    assert response.status_code == 302

    # E/G: case-insensitive registration fulfills both pending assignments.
    both_client = app.test_client()
    response = both_client.post('/register', data={
        'name': 'Both Courses Student',
        'email': both_email.upper(),
        'password': password,
        'confirm_password': password,
    })
    assert response.status_code == 302

    with app.app_context():
        pending_user = User.query.filter_by(email=pending_email.lower()).first()
        both_user = User.query.filter_by(email=both_email.lower()).first()
        assert pending_user.role == 'student'
        assert pending_user.name == 'Pending Student'
        assert [e.course_id for e in pending_user.enrollments if e.is_active] == [python_course_id]
        assert {e.course_id for e in both_user.enrollments if e.is_active} == {
            python_course_id, genai_course_id
        }
        assert PendingCourseAssignment.query.filter_by(
            email=pending_email.lower(), is_active=True
        ).count() == 0
        assert PendingCourseAssignment.query.filter_by(
            email=both_email.lower(), is_active=True
        ).count() == 0
        assert check_password_hash(pending_user.password_hash, password)
        assert pending_user.password_hash != password

    # L/M/N: password verification and inactive account handling.
    wrong = pending_client.post('/login', data={
        'email': pending_email.upper(), 'password': 'wrong-password'
    })
    assert wrong.status_code == 200
    correct = pending_client.post('/login', data={
        'email': pending_email.upper(), 'password': password
    })
    assert correct.status_code == 302
    pending_client.get('/logout')
    inactive_response = pending_client.post('/login', data={
        'email': inactive_email, 'password': password
    })
    assert inactive_response.status_code == 200

    # K: a Python-only student cannot access Generative AI by URL.
    assert pending_client.post('/login', data={
        'email': pending_email, 'password': password
    }).status_code == 302
    access_response = pending_client.get(f'/course/{genai_course_id}')
    assert access_response.status_code == 403

    with app.app_context():
        pending_user = User.query.filter_by(email=pending_email.lower()).first()
        both_user = User.query.filter_by(email=both_email.lower()).first()
        existing_user = User.query.filter_by(email=existing_email).first()
        inactive_user = User.query.filter_by(email=inactive_email).first()
        db.session.query(CourseEnrollment).filter(
            CourseEnrollment.user_id.in_([
                pending_user.id, both_user.id, existing_user.id, inactive_user.id
            ])
        ).delete(synchronize_session=False)
        db.session.delete(pending_user)
        db.session.delete(both_user)
        db.session.delete(existing_user)
        db.session.delete(inactive_user)
        db.session.commit()

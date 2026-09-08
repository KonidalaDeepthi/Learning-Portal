from app import create_app
from app.extensions import db
from app.models.course import Course, CourseEnrollment
from app.models.user import User


def test_email_authentication_and_course_access():
    app = create_app('development')
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        admin = User.query.filter_by(
            email=app.config['MENTOR_ADMIN_EMAIL']
        ).first()
        python_course = Course.query.filter_by(name='Python Full Stack').first()
        assert admin is not None
        assert python_course is not None

    client = app.test_client()
    assert client.post('/login', data={
        'email': app.config['MENTOR_ADMIN_EMAIL'],
    }, follow_redirects=True).status_code == 200

    response = client.post('/mentor/students/create', data={
        'name': 'Managed Student',
        'email': '  managed-email@example.com  ',
        'course_id': python_course.id,
    })
    assert response.status_code == 302

    with app.app_context():
        student = User.query.filter_by(email='managed-email@example.com').first()
        assert student is not None
        assert student.is_student is True
        assert student.is_active is True
        assert CourseEnrollment.query.filter_by(
            user_id=student.id,
            course_id=python_course.id,
            is_active=True,
        ).count() == 1

    client.get('/logout')
    assert client.post('/login', data={
        'email': 'MANAGED-EMAIL@EXAMPLE.COM',
    }).status_code == 302
    assert b'Python Full Stack' in client.get('/courses').data

    client.get('/logout')
    unknown = client.post('/login', data={'email': 'unknown@example.com'})
    assert unknown.status_code == 200
    assert b'This email is not registered' in unknown.data

    with app.app_context():
        student = User.query.filter_by(email='managed-email@example.com').first()
        CourseEnrollment.query.filter_by(user_id=student.id).delete(
            synchronize_session=False
        )
        db.session.delete(student)
        db.session.commit()

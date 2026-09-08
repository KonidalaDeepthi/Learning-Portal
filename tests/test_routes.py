"""
Simplified test — verifies the core security model works.
"""
import sys
sys.path.insert(0, 'd:/Mentor')

from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash
import re

app = create_app('development')

print("=" * 52)
print("  LearnSpace — Core Security & Route Tests")
print("=" * 52)

with app.app_context():
    # Pre-create a test student directly in DB (bypass CSRF in test)
    existing = User.query.filter_by(email='teststudent@test.com').first()
    if not existing:
        student = User(
            name='Test Student',
            email='teststudent@test.com',
            password_hash=generate_password_hash('Password123!'),
            role='student',
            is_active=True
        )
        db.session.add(student)
        db.session.commit()
        print("✓ Test student created in DB")
    else:
        print("✓ Test student already exists")

# Use WTF_CSRF_ENABLED=False for testing
app.config['WTF_CSRF_ENABLED'] = False

with app.test_client() as c:
    with app.app_context():
        
        # ── Basic page loads ──
        assert c.get('/login').status_code == 200
        print("✓ /login: 200 OK")
        
        assert c.get('/register').status_code == 404
        print("✓ /register: public registration disabled")

        # ── Unauthenticated redirects ──
        for url in ['/home', '/courses', '/profile', '/progress', '/account', '/chat',
                    '/mentor/dashboard', '/mentor/students', '/mentor/courses']:
            r = c.get(url)
            assert r.status_code == 302, f"{url} should redirect, got {r.status_code}"
            assert '/login' in r.headers.get('Location', ''), f"{url} should redirect to login"
        print("✓ All 9 protected routes redirect unauthenticated users to /login")

        # ── Mentor admin login → dashboard ──
        admin_email = app.config['MENTOR_ADMIN_EMAIL']
        admin_pass  = app.config['MENTOR_ADMIN_PASSWORD']
        
        r = c.post('/login', data={'email': admin_email, 'password': admin_pass})
        assert r.status_code == 302
        assert 'mentor/dashboard' in r.headers.get('Location', '')
        print(f"✓ Mentor login → redirects to /mentor/dashboard")

        # ── Mentor accesses dashboard ──
        r = c.get('/mentor/dashboard')
        assert r.status_code == 200, f"Dashboard returned {r.status_code}"
        print("✓ Mentor dashboard: 200 OK")

        # ── Mentor accesses all their pages ──
        for url in ['/mentor/students', '/mentor/courses', '/mentor/quizzes',
                    '/mentor/videos', '/mentor/updates', '/mentor/messages', '/mentor/announcements']:
            r = c.get(url)
            assert r.status_code == 200, f"{url} returned {r.status_code}"
            print(f"✓ {url}: 200 OK")

        # ── Logout ──
        logout_response = c.get('/logout')
        assert logout_response.status_code == 302
        assert logout_response.headers['Location'] == '/login'
        assert c.get('/login').status_code == 200
        r = c.get('/mentor/dashboard')
        assert r.status_code == 302
        print("✓ After logout, /mentor/dashboard redirects again")

        # ── Student login ──
        r = c.post('/login', data={'email': 'teststudent@test.com', 'password': 'Password123!'})
        assert r.status_code == 302
        assert 'home' in r.headers.get('Location', '')
        print("✓ Student login → redirects to /home")

        # ── Student accesses their pages ──
        for url in ['/home', '/courses', '/profile', '/progress', '/account']:
            r = c.get(url)
            assert r.status_code == 200, f"Student {url} returned {r.status_code}"
            print(f"✓ Student {url}: 200 OK")

        # ── Student CANNOT access mentor pages → 403 ──
        for url in ['/mentor/dashboard', '/mentor/students', '/mentor/courses']:
            r = c.get(url)
            assert r.status_code == 403, f"Student {url} should be 403, got {r.status_code}"
            print(f"✓ Student blocked from {url}: 403 Forbidden")

        student_logout = c.get('/logout')
        assert student_logout.status_code == 302
        assert student_logout.headers['Location'] == '/login'
        assert c.get('/login').status_code == 200
        assert '/login' in c.get('/home').headers.get('Location', '')
        print("✓ Student one-click logout clears the session")

        # ── Wrong password → stays on login ──
        r = c.post('/login', data={'email': admin_email, 'password': 'wrongpassword'})
        assert r.status_code == 200  # stays on login page
        print("✓ Wrong password → stays on login page (200)")

print()
print("=" * 52)
print("  ✅  ALL TESTS PASSED!")
print("=" * 52)
print()
print(f"  🌐 Open browser: http://127.0.0.1:5000")
print(f"  👤 Mentor email: {app.config['MENTOR_ADMIN_EMAIL']}")
print(f"  🔑 Password: (from your .env file)")

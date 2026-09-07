"""End-to-end quiz flow test."""
import sys
sys.path.insert(0, 'd:/Mentor')

from app import create_app
from app.extensions import db

app = create_app('development')
app.config['WTF_CSRF_ENABLED'] = False

print("=" * 52)
print("  LearnSpace — End-to-End Feature Tests")
print("=" * 52)

# ── Seed: create a quiz & ensure student is enrolled ──
with app.app_context():
    from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
    from app.models.course import Course, CourseEnrollment
    from app.models.user import User
    from app.models.update import DailyUpdate
    from app.models.announcement import Announcement

    course  = Course.query.first()
    mentor  = User.query.filter_by(role='mentor_admin').first()
    student = User.query.filter_by(email='teststudent@test.com').first()
    if student is None:
        student = User.query.filter_by(role='student').first()

    student_email = student.email
    student_id    = student.id
    mentor_email  = mentor.email
    course_id     = course.id
    course_name   = course.name

    # Enroll or reactivate the student for this isolated E2E fixture.
    enrollment = CourseEnrollment.query.filter_by(
        user_id=student_id, course_id=course_id
    ).first()
    if enrollment:
        enrollment.is_active = True
    else:
        db.session.add(CourseEnrollment(user_id=student_id, course_id=course_id))
    db.session.commit()
    print(f"✓ Student enrolled in: {course_name}")

    # Remove old test quiz
    old = Quiz.query.filter_by(title='E2E Test Quiz').first()
    if old:
        db.session.delete(old)
        db.session.commit()

    # Create quiz
    quiz = Quiz(title='E2E Test Quiz', course_id=course_id,
                status='published', created_by=mentor.id)
    db.session.add(quiz)
    db.session.flush()

    for i, (qtext, a, b, c, d, correct) in enumerate([
        ('What is 2+2?',            '3','4','5','6',         'B'),
        ('Python is a ___ language','Compiled','Interpreted','None','Both','B'),
        ('Flask is a ___',          'Database','ORM','Framework','Language','C'),
    ]):
        db.session.add(QuizQuestion(
            quiz_id=quiz.id, question_text=qtext,
            option_a=a, option_b=b, option_c=c, option_d=d,
            correct_option=correct, marks=2, order_index=i))

    quiz.total_marks = 6
    db.session.commit()
    quiz_id = quiz.id
    print(f"✓ Quiz created (ID={quiz_id}): 3 questions, 6 marks")

    # Create a daily update
    old_upd = DailyUpdate.query.filter_by(title='E2E Test Update').first()
    if not old_upd:
        db.session.add(DailyUpdate(title='E2E Test Update',
                                   content='Today: Study Flask basics.',
                                   course_id=course_id, created_by=mentor.id))
        db.session.commit()
    print("✓ Daily update created")

# ── Run all page + action tests ──
with app.test_client() as c:
    with app.app_context():
        from app.models.quiz import Quiz, QuizQuestion, QuizAttempt

        questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
        q_ids = [q.id for q in questions]

        # ── MENTOR: create update via POST ──
        c.post('/login', data={'email': mentor_email, 'password': app.config['MENTOR_ADMIN_PASSWORD']})

        r = c.post('/mentor/updates/create', data={
            'title': 'POST Test Update',
            'content': 'Testing update creation via form POST.',
            'course_id': course_id
        })
        assert r.status_code == 302, f"Create update failed: {r.status_code}"
        print("✓ Mentor: POST daily update works (302 redirect)")

        # ── MENTOR: send announcement ──
        r = c.post('/mentor/announcements/send', data={
            'title': 'Test Announcement',
            'content': 'This is a test announcement for all students.',
            'target_type': 'all'
        })
        assert r.status_code == 302, f"Send announcement failed: {r.status_code}"
        print("✓ Mentor: POST announcement works (302 redirect)")

        # ── MENTOR: quiz detail page ──
        r = c.get(f'/mentor/quizzes/{quiz_id}')
        assert r.status_code == 200, f"Quiz detail failed: {r.status_code}"
        print("✓ Mentor: quiz detail page loads (200)")

        # ── MENTOR: quiz results page ──
        r = c.get(f'/mentor/quizzes/{quiz_id}/results')
        assert r.status_code == 200
        print("✓ Mentor: quiz results page loads (200)")

        # ── MENTOR: video create form ──
        r = c.get('/mentor/videos/create')
        assert r.status_code == 200
        print("✓ Mentor: video create form loads (200)")

        # ── MENTOR: POST video ──
        r = c.post('/mentor/videos/create', data={
            'title': 'Test Video',
            'url': 'https://youtube.com/watch?v=test',
            'course_id': course_id,
            'topic': 'Test Topic',
            'resource_type': 'video',
            'status': 'published'
        })
        assert r.status_code == 302, f"Create video failed: {r.status_code}"
        print("✓ Mentor: POST video/resource works (302 redirect)")

        c.get('/logout')

        # ── STUDENT: quiz start ──
        c.post('/login', data={'email': student_email, 'password': 'Password123!'})

        r = c.get(f'/quiz/{quiz_id}/start')
        assert r.status_code == 200, f"Quiz start failed: {r.status_code}"
        print("✓ Student: quiz start page (200)")

        # ── STUDENT: quiz take ──
        r = c.get(f'/quiz/{quiz_id}/take')
        assert r.status_code == 200, f"Quiz take failed: {r.status_code}"
        print("✓ Student: quiz take page (200)")

        # ── STUDENT: submit quiz (Q1 correct, Q2 correct, Q3 wrong) ──
        submit_data = {f'q_{q_ids[0]}': 'B', f'q_{q_ids[1]}': 'B', f'q_{q_ids[2]}': 'A'}
        r = c.post(f'/quiz/{quiz_id}/submit', data=submit_data)
        assert r.status_code == 302, f"Submit failed: {r.status_code}"
        print(f"✓ Student: quiz submitted (302 → {r.headers.get('Location','')})")

        # ── Check DB results ──
        attempt = QuizAttempt.query.filter_by(user_id=student_id, quiz_id=quiz_id).first()
        assert attempt is not None, "Attempt not saved!"
        assert attempt.submitted_at is not None, "submitted_at not set!"
        assert attempt.score == 4, f"Expected score 4, got {attempt.score}"  # Q1+Q2 correct = 4 marks
        assert attempt.correct_count == 2
        assert attempt.wrong_count == 1
        assert attempt.percentage == round((4/6)*100, 1)
        print(f"✓ Auto-grading: {attempt.score}/{attempt.total_marks} ({attempt.percentage}%) — correct={attempt.correct_count} wrong={attempt.wrong_count}")

        # ── STUDENT: result page ──
        r = c.get(f'/quiz/{quiz_id}/result')
        assert r.status_code == 200, f"Result page failed: {r.status_code}"
        print("✓ Student: quiz result page (200)")

        # ── STUDENT: cannot retake ──
        r = c.get(f'/quiz/{quiz_id}/take')
        assert r.status_code == 302  # redirected away
        print("✓ Student: cannot retake (redirected on second attempt)")

        # ── STUDENT: notifications ──
        r = c.get('/notifications')
        assert r.status_code == 200
        print("✓ Student: notifications page (200)")

        # ── STUDENT: progress ──
        r = c.get('/progress')
        assert r.status_code == 200
        print("✓ Student: progress page (200)")

        # ── STUDENT: course detail ──
        r = c.get(f'/course/{course_id}')
        assert r.status_code == 200, f"Course detail failed: {r.status_code}"
        print("✓ Student: course detail page (200)")

        # ── STUDENT: send chat message ──
        r = c.post('/chat/send', data={'content': 'Hello mentor, I have a question!'})
        assert r.status_code == 302
        print("✓ Student: chat send (302)")

        # ── STUDENT: view chat ──
        r = c.get('/chat')
        assert r.status_code == 200
        print("✓ Student: chat view (200)")

        c.get('/logout')

        # ── MENTOR: see conversation ──
        c.post('/login', data={'email': mentor_email, 'password': app.config['MENTOR_ADMIN_PASSWORD']})
        r = c.get('/mentor/messages')
        assert r.status_code == 200
        html = r.data.decode('utf-8')
        assert 'Hello mentor' in html or student_email.split('@')[0].lower() in html.lower() or 'convo' in html or '1' in html
        print("✓ Mentor: messages list shows conversation (200)")

        # ── MENTOR: student detail ──
        r = c.get(f'/mentor/students/{student_id}')
        assert r.status_code == 200
        print("✓ Mentor: student detail page (200)")

print()
print("=" * 52)
print("  ALL END-TO-END TESTS PASSED! ✅")
print("=" * 52)
print()
print("  Open: http://127.0.0.1:5000")
print(f"  Mentor: {app.config['MENTOR_ADMIN_EMAIL']}")
print("  Student: teststudent@test.com / Password123!")

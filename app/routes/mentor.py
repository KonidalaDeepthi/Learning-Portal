"""
app/routes/mentor.py — Mentor/Admin Routes (COMPLETE)
=======================================================
ALL routes here are protected by:
1. @login_required  -> must be logged in
2. @mentor_admin_required -> role must be 'mentor_admin'
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.decorators import mentor_admin_required
from app.extensions import db

mentor_bp = Blueprint('mentor', __name__, url_prefix='/mentor')


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────
@mentor_bp.route('/dashboard')
@login_required
@mentor_admin_required
def dashboard():
    from app.models.user import User
    from app.models.course import Course
    from app.models.quiz import Quiz, QuizAttempt
    from app.models.video import Video
    from datetime import timedelta

    total_students   = User.query.filter_by(role='student').count()
    active_students  = User.query.filter_by(role='student', is_active=True).count()
    total_courses    = Course.query.filter_by(status='active').count()
    total_quizzes    = Quiz.query.filter_by(status='published').count()
    total_attempts   = QuizAttempt.query.count()
    total_videos     = Video.query.filter_by(status='published').count()

    courses         = Course.query.all()
    recent_students = User.query.filter_by(role='student').order_by(
        User.created_at.desc()).limit(5).all()
    recent_attempts = QuizAttempt.query.filter(
        QuizAttempt.submitted_at.isnot(None)
    ).order_by(QuizAttempt.submitted_at.desc()).limit(6).all()

    # ── Chart data 1: quiz attempts per day (last 7 days) ──
    today = datetime.utcnow().date()
    attempts_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = QuizAttempt.query.filter(
            db.func.date(QuizAttempt.submitted_at) == day
        ).count()
        attempts_by_day.append({'label': day.strftime('%a'), 'count': count})

    # ── Chart data 2: students per course ──
    students_per_course = [
        {'name': c.name, 'count': c.get_student_count()}
        for c in courses
    ]

    return render_template('mentor/dashboard.html',
                           total_students=total_students,
                           active_students=active_students,
                           total_courses=total_courses,
                           total_quizzes=total_quizzes,
                           total_attempts=total_attempts,
                           total_videos=total_videos,
                           courses=courses,
                           recent_students=recent_students,
                           recent_attempts=recent_attempts,
                           attempts_by_day=attempts_by_day,
                           students_per_course=students_per_course)


# ─────────────────────────────────────────
# STUDENTS
# ─────────────────────────────────────────
@mentor_bp.route('/students')
@login_required
@mentor_admin_required
def students():
    from app.models.user import User
    from app.models.course import Course
    search      = request.args.get('search', '').strip().lower()
    course_filter = request.args.get('course_id', '')

    query = User.query.filter_by(role='student')
    if search:
        query = query.filter(
            db.or_(User.name.ilike(f'%{search}%'),
                   User.email.ilike(f'%{search}%'))
        )
    if course_filter:
        from app.models.course import CourseEnrollment
        query = query.join(CourseEnrollment).filter(
            CourseEnrollment.course_id == int(course_filter),
            CourseEnrollment.is_active.is_(True)
        )
    students_list = query.order_by(User.created_at.desc()).all()
    courses = Course.query.filter_by(status='active').all()

    return render_template('mentor/students.html',
                           students=students_list,
                           courses=courses,
                           search=search,
                           course_filter=course_filter)


@mentor_bp.route('/students/create', methods=['POST'])
@login_required
@mentor_admin_required
def create_student():
    from app.models.course import Course
    from app.course_access import create_student_account, normalize_email

    name = request.form.get('name', '').strip()
    email = normalize_email(request.form.get('email', ''))
    password = request.form.get('password', '')
    course_id = request.form.get('course_id', type=int)
    course = Course.query.filter_by(id=course_id, status='active').first() if course_id else None

    if len(name) < 2:
        flash('Please enter the student name.', 'danger')
    elif not email or '@' not in email or ' ' in email:
        flash('Please enter a valid student email.', 'danger')
    elif len(password) < 8:
        flash('Password must be at least 8 characters long.', 'danger')
    elif not course:
        flash('Please select an active course.', 'danger')
    else:
        try:
            result, student = create_student_account(name, email, password, course)
            if result == 'not_student':
                db.session.rollback()
                flash('This email belongs to a non-student account.', 'warning')
            else:
                db.session.commit()
                message = 'Student account created.' if result == 'created' else 'Existing student updated.'
                flash(f'{message} Active access granted to {course.name}.', 'success')
                return redirect(url_for('mentor.student_detail', student_id=student.id))
        except SQLAlchemyError:
            db.session.rollback()
            flash('Student account could not be saved. No changes were made.', 'danger')

    return redirect(url_for('mentor.students'))


@mentor_bp.route('/course-access')
@login_required
@mentor_admin_required
def course_access():
    return redirect(url_for('mentor.students', course_id=request.args.get('course_id', '')))


@mentor_bp.route('/students/assign-course', methods=['POST'])
@login_required
@mentor_admin_required
def assign_student_to_course():
    from app.models.course import Course
    from app.course_access import assign_course_by_email, normalize_email

    email = normalize_email(request.form.get('email', ''))
    course_id = request.form.get('course_id', type=int)
    course = Course.query.filter_by(id=course_id, status='active').first() if course_id else None

    if not email or ' ' in email or '@' not in email:
        flash('Please enter a valid student email.', 'danger')
    elif not course:
        flash('Please select an active course.', 'danger')
    else:
        result, student = assign_course_by_email(email, course, current_user.id)
        if result == 'not_student':
            flash('This email belongs to a non-student account.', 'warning')
        elif result == 'enrolled':
            db.session.commit()
            flash(f'{email} now has active access to {course.name}.', 'success')
        else:
            db.session.commit()
            flash('Student account not found. Create the student account first.', 'warning')

    return redirect(url_for('mentor.students', search=email))


@mentor_bp.route('/students/<int:student_id>')
@login_required
@mentor_admin_required
def student_detail(student_id):
    from app.models.user import User
    from app.models.quiz import QuizAttempt
    student  = User.query.filter_by(id=student_id, role='student').first_or_404()
    attempts = QuizAttempt.query.filter_by(user_id=student_id).order_by(
        QuizAttempt.submitted_at.desc()).all()
    enrolled_courses = student.get_enrolled_courses()
    return render_template('mentor/student_detail.html',
                           student=student,
                           attempts=attempts,
                           enrolled_courses=enrolled_courses)


@mentor_bp.route('/students/<int:student_id>/toggle-active', methods=['POST'])
@login_required
@mentor_admin_required
def toggle_student_active(student_id):
    from app.models.user import User
    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    student.is_active = not student.is_active
    db.session.commit()
    status = 'activated' if student.is_active else 'deactivated'
    flash(f'{student.name} has been {status}.', 'success')
    return redirect(url_for('mentor.student_detail', student_id=student_id))


@mentor_bp.route('/students/<int:student_id>/reset-password', methods=['POST'])
@login_required
@mentor_admin_required
def reset_student_password(student_id):
    from werkzeug.security import generate_password_hash
    from app.models.user import User

    student = User.query.filter_by(id=student_id, role='student').first_or_404()
    password = request.form.get('password', '')
    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'danger')
    else:
        try:
            student.password_hash = generate_password_hash(password)
            db.session.commit()
            flash('Student password has been reset.', 'success')
        except SQLAlchemyError:
            db.session.rollback()
            flash('Password reset failed. No changes were made.', 'danger')
    return redirect(url_for('mentor.student_detail', student_id=student_id))


# ─────────────────────────────────────────
# COURSES
# ─────────────────────────────────────────
@mentor_bp.route('/courses')
@login_required
@mentor_admin_required
def courses():
    from app.models.course import Course
    courses_list = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('mentor/courses.html', courses=courses_list)


@mentor_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@mentor_admin_required
def create_course():
    from app.models.course import Course
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not name:
            flash('Course name is required.', 'danger')
            return render_template('mentor/course_form.html')
        if Course.query.filter_by(name=name).first():
            flash('A course with this name already exists.', 'warning')
            return render_template('mentor/course_form.html')
        course = Course(name=name, description=description,
                        status='active', created_by=current_user.id)
        db.session.add(course)
        db.session.commit()
        flash(f'Course "{name}" created successfully!', 'success')
        return redirect(url_for('mentor.course_detail', course_id=course.id))
    return render_template('mentor/course_form.html')


@mentor_bp.route('/courses/<int:course_id>')
@login_required
@mentor_admin_required
def course_detail(course_id):
    from app.models.course import Course
    from app.models.quiz import Quiz
    from app.models.video import Video
    course      = Course.query.get_or_404(course_id)
    enrollments = course.enrollments.all()
    quizzes     = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.created_at.desc()).all()
    videos      = Video.query.filter_by(course_id=course_id).order_by(
        Video.day_number.asc(), Video.order_index.asc(), Video.id.asc()).all()
    return render_template('mentor/course_detail.html',
                           course=course,
                           enrollments=enrollments,
                           quizzes=quizzes,
                           videos=videos)


@mentor_bp.route('/courses/<int:course_id>/add-student', methods=['POST'])
@login_required
@mentor_admin_required
def add_student_to_course(course_id):
    from app.models.course import Course
    from app.course_access import assign_course_by_email, normalize_email
    course = Course.query.get_or_404(course_id)
    email = normalize_email(request.form.get('email', ''))
    if not email or '@' not in email or ' ' in email:
        flash('Please enter a valid student email.', 'danger')
        return redirect(url_for('mentor.course_detail', course_id=course_id))
    result, student = assign_course_by_email(email, course, current_user.id)
    if result == 'not_student':
        flash('This email belongs to a non-student account.', 'warning')
    elif result == 'enrolled':
        flash(f'{email} now has active access to {course.name}.', 'success')
    else:
        flash('Student account not found. Create the student account first.', 'warning')
    db.session.commit()
    return redirect(url_for('mentor.course_detail', course_id=course_id))


@mentor_bp.route('/courses/<int:course_id>/remove-student/<int:student_id>', methods=['POST'])
@login_required
@mentor_admin_required
def remove_student_from_course(course_id, student_id):
    from app.models.course import CourseEnrollment
    enrollment = CourseEnrollment.query.filter_by(
        user_id=student_id, course_id=course_id).first_or_404()
    enrollment.is_active = False
    db.session.commit()
    flash('Student access has been deactivated.', 'info')
    return redirect(url_for('mentor.course_detail', course_id=course_id))


@mentor_bp.route('/courses/<int:course_id>/restore-student/<int:student_id>', methods=['POST'])
@login_required
@mentor_admin_required
def restore_student_to_course(course_id, student_id):
    from app.models.course import CourseEnrollment
    enrollment = CourseEnrollment.query.filter_by(
        user_id=student_id, course_id=course_id).first_or_404()
    enrollment.is_active = True
    db.session.commit()
    flash('Student access has been reactivated.', 'success')
    return redirect(url_for('mentor.course_detail', course_id=course_id))


# ─────────────────────────────────────────
# QUIZZES — Full CRUD
# ─────────────────────────────────────────
@mentor_bp.route('/quizzes')
@login_required
@mentor_admin_required
def quizzes():
    from app.models.quiz import Quiz
    quizzes_list = Quiz.query.order_by(Quiz.course_id.asc(), Quiz.day_number.asc(), Quiz.id.asc()).all()
    return render_template('mentor/quizzes.html', quizzes=quizzes_list)


@mentor_bp.route('/quizzes/create', methods=['GET', 'POST'])
@login_required
@mentor_admin_required
def create_quiz():
    from app.models.course import Course
    from app.models.quiz import Quiz
    courses = Course.query.filter_by(status='active').all()

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        course_id   = request.form.get('course_id', type=int)
        time_limit  = request.form.get('time_limit_minutes', 0, type=int)

        if not title or not course_id:
            flash('Title and course are required.', 'danger')
            return render_template('mentor/quiz_form.html', courses=courses)

        quiz = Quiz(
            title=title,
            description=description,
            course_id=course_id,
            time_limit_minutes=time_limit,
            status='draft',
            created_by=current_user.id
        )
        db.session.add(quiz)
        db.session.commit()
        flash(f'Quiz "{title}" created! Now add questions.', 'success')
        return redirect(url_for('mentor.quiz_detail', quiz_id=quiz.id))

    return render_template('mentor/quiz_form.html', courses=courses)


@mentor_bp.route('/quizzes/<int:quiz_id>')
@login_required
@mentor_admin_required
def quiz_detail(quiz_id):
    from app.models.quiz import Quiz, QuizAttempt
    quiz      = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions.all()
    attempts  = QuizAttempt.query.filter_by(quiz_id=quiz_id).filter(
        QuizAttempt.submitted_at.isnot(None)
    ).order_by(QuizAttempt.submitted_at.desc()).all()
    return render_template('mentor/quiz_detail.html',
                           quiz=quiz,
                           questions=questions,
                           attempts=attempts)


@mentor_bp.route('/quizzes/<int:quiz_id>/add-question', methods=['POST'])
@login_required
@mentor_admin_required
def add_question(quiz_id):
    from app.models.quiz import Quiz, QuizQuestion
    quiz = Quiz.query.get_or_404(quiz_id)

    question_text  = request.form.get('question_text', '').strip()
    option_a       = request.form.get('option_a', '').strip()
    option_b       = request.form.get('option_b', '').strip()
    option_c       = request.form.get('option_c', '').strip()
    option_d       = request.form.get('option_d', '').strip()
    correct_option = request.form.get('correct_option', '').upper()
    explanation    = request.form.get('explanation', '').strip()
    marks          = request.form.get('marks', 1, type=int)

    if not all([question_text, option_a, option_b, option_c, option_d, correct_option, explanation]):
        flash('All fields are required for a question.', 'danger')
        return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))

    if correct_option not in ['A', 'B', 'C', 'D']:
        flash('Correct option must be A, B, C, or D.', 'danger')
        return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))

    order = quiz.questions.count()
    question = QuizQuestion(
        quiz_id=quiz_id,
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option,
        explanation=explanation,
        marks=marks,
        order_index=order
    )
    db.session.add(question)

    # Recalculate total marks
    db.session.flush()
    quiz.total_marks = quiz.calculate_total_marks()
    db.session.commit()

    flash('Question added successfully!', 'success')
    return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))


@mentor_bp.route('/quizzes/<int:quiz_id>/edit-question/<int:question_id>', methods=['POST'])
@login_required
@mentor_admin_required
def edit_question(quiz_id, question_id):
    from app.models.quiz import Quiz, QuizQuestion
    question = QuizQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first_or_404()
    question.question_text = request.form.get('question_text', '').strip()
    question.option_a = request.form.get('option_a', '').strip()
    question.option_b = request.form.get('option_b', '').strip()
    question.option_c = request.form.get('option_c', '').strip()
    question.option_d = request.form.get('option_d', '').strip()
    question.correct_option = request.form.get('correct_option', '').upper()
    question.explanation = request.form.get('explanation', '').strip()
    question.marks = request.form.get('marks', 1, type=int)
    if (not all([question.question_text, question.option_a, question.option_b,
                 question.option_c, question.option_d, question.explanation]) or
            question.correct_option not in {'A', 'B', 'C', 'D'}):
        flash('Every question field and a valid correct answer are required.', 'danger')
        return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.total_marks = quiz.calculate_total_marks()
    db.session.commit()
    flash('Question updated successfully.', 'success')
    return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))


@mentor_bp.route('/quizzes/<int:quiz_id>/delete-question/<int:question_id>', methods=['POST'])
@login_required
@mentor_admin_required
def delete_question(quiz_id, question_id):
    from app.models.quiz import Quiz, QuizQuestion
    question = QuizQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first_or_404()
    db.session.delete(question)
    db.session.flush()
    quiz = Quiz.query.get(quiz_id)
    quiz.total_marks = quiz.calculate_total_marks()
    db.session.commit()
    flash('Question deleted.', 'info')
    return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))


@mentor_bp.route('/quizzes/<int:quiz_id>/publish', methods=['POST'])
@login_required
@mentor_admin_required
def publish_quiz(quiz_id):
    from app.models.quiz import Quiz
    from app.models.course import CourseEnrollment
    from app.models.announcement import Notification
    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.questions.count() == 0:
        flash('Cannot publish a quiz with no questions!', 'danger')
        return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))

    quiz.status = 'published'
    quiz.total_marks = quiz.calculate_total_marks()

    # Notify all enrolled students
    enrollments = CourseEnrollment.query.filter_by(
        course_id=quiz.course_id, is_active=True).all()
    for enrollment in enrollments:
        notif = Notification(
            user_id=enrollment.user_id,
            title=f'New Quiz: {quiz.title}',
            content=f'A new quiz has been published in {quiz.course.name}. Good luck!',
            type='quiz',
            related_id=quiz_id
        )
        db.session.add(notif)

    db.session.commit()
    flash(f'Quiz "{quiz.title}" published! Students have been notified.', 'success')
    return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))


@mentor_bp.route('/quizzes/<int:quiz_id>/unpublish', methods=['POST'])
@login_required
@mentor_admin_required
def unpublish_quiz(quiz_id):
    from app.models.quiz import Quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.status = 'draft'
    db.session.commit()
    flash(f'Quiz "{quiz.title}" moved back to draft.', 'info')
    return redirect(url_for('mentor.quiz_detail', quiz_id=quiz_id))


@mentor_bp.route('/quizzes/<int:quiz_id>/delete', methods=['POST'])
@login_required
@mentor_admin_required
def delete_quiz(quiz_id):
    from app.models.quiz import Quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    title = quiz.title
    db.session.delete(quiz)
    db.session.commit()
    flash(f'Quiz "{title}" deleted.', 'info')
    return redirect(url_for('mentor.quizzes'))


@mentor_bp.route('/quizzes/<int:quiz_id>/results')
@login_required
@mentor_admin_required
def quiz_results(quiz_id):
    from app.models.quiz import Quiz, QuizAttempt
    quiz     = Quiz.query.get_or_404(quiz_id)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).filter(
        QuizAttempt.submitted_at.isnot(None)
    ).order_by(QuizAttempt.submitted_at.desc()).all()

    # Stats
    if attempts:
        scores      = [a.percentage for a in attempts]
        avg_score   = sum(scores) / len(scores)
        high_score  = max(scores)
        pass_count  = sum(1 for s in scores if s >= 50)
    else:
        avg_score = high_score = pass_count = 0

    return render_template('mentor/quiz_results.html',
                           quiz=quiz,
                           attempts=attempts,
                           avg_score=avg_score,
                           high_score=high_score,
                           pass_count=pass_count)


@mentor_bp.route('/results')
@login_required
@mentor_admin_required
def results():
    from app.models.course import Course
    from app.models.quiz import Quiz, QuizAttempt
    from app.models.user import User

    student_id = request.args.get('student_id', type=int)
    quiz_id = request.args.get('quiz_id', type=int)
    query = QuizAttempt.query.filter(QuizAttempt.submitted_at.isnot(None))
    if student_id:
        query = query.filter_by(user_id=student_id)
    if quiz_id:
        query = query.filter_by(quiz_id=quiz_id)
    attempts = query.order_by(QuizAttempt.submitted_at.desc()).all()
    students = User.query.filter_by(role='student').order_by(User.name).all()
    quizzes_list = Quiz.query.join(Course).order_by(
        Course.name, Quiz.day_number, Quiz.id).all()
    return render_template('mentor/results.html', attempts=attempts,
                           students=students, quizzes=quizzes_list,
                           student_id=student_id, quiz_id=quiz_id)


# ─────────────────────────────────────────
# VIDEOS / RESOURCES
# ─────────────────────────────────────────
@mentor_bp.route('/videos')
@login_required
@mentor_admin_required
def videos():
    from app.models.video import Video
    course_filter = request.args.get('course_id', '', type=str)
    query = Video.query
    if course_filter:
        query = query.filter_by(course_id=int(course_filter))
    videos_list = query.order_by(Video.course_id.asc(), Video.day_number.asc(),
                                 Video.order_index.asc(), Video.id.asc()).all()
    from app.models.course import Course
    courses = Course.query.filter_by(status='active').all()
    return render_template('mentor/videos.html', videos=videos_list, courses=courses,
                           course_filter=course_filter)


@mentor_bp.route('/videos/create', methods=['GET', 'POST'])
@login_required
@mentor_admin_required
def create_video():
    from app.models.course import Course
    from app.models.video import Video
    from app.models.announcement import Notification
    from app.models.course import CourseEnrollment
    courses = Course.query.filter_by(status='active').all()

    if request.method == 'POST':
        title         = request.form.get('title', '').strip()
        url           = request.form.get('url', '').strip()
        course_id     = request.form.get('course_id', type=int)
        description   = request.form.get('description', '').strip()
        topic         = request.form.get('topic', '').strip()
        day_number    = request.form.get('day_number', type=int)
        resource_type = request.form.get('resource_type', 'video')
        status        = request.form.get('status', 'draft')

        if not all([title, url, course_id]):
            flash('Title, URL and course are required.', 'danger')
            return render_template('mentor/video_form.html', courses=courses)

        video = Video(
            title=title,
            url=url,
            course_id=course_id,
            description=description,
            topic=topic,
            day_number=day_number,
            order_index=day_number or 0,
            resource_type=resource_type,
            status=status,
            created_by=current_user.id
        )
        db.session.add(video)

        # Notify students if published immediately
        if status == 'published':
            enrollments = CourseEnrollment.query.filter_by(
                course_id=course_id, is_active=True).all()
            for e in enrollments:
                db.session.add(Notification(
                    user_id=e.user_id,
                    title=f'New Resource: {title}',
                    content=f'A new {resource_type} has been added to your course.',
                    type='video',
                ))

        db.session.commit()
        flash(f'Resource "{title}" added successfully!', 'success')
        return redirect(url_for('mentor.videos'))

    return render_template('mentor/video_form.html', courses=courses)


@mentor_bp.route('/videos/<int:video_id>/edit', methods=['GET', 'POST'])
@login_required
@mentor_admin_required
def edit_video(video_id):
    from app.models.course import Course
    from app.models.video import Video
    video = Video.query.get_or_404(video_id)
    courses = Course.query.filter_by(status='active').all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        url = request.form.get('url', '').strip()
        course_id = request.form.get('course_id', type=int)
        day_number = request.form.get('day_number', type=int)
        if not all([title, url, course_id]):
            flash('Title, URL and course are required.', 'danger')
            return render_template('mentor/video_form.html', courses=courses, video=video)

        video.title = title
        video.url = url
        video.course_id = course_id
        video.day_number = day_number
        video.order_index = day_number or 0
        video.description = request.form.get('description', '').strip()
        video.topic = request.form.get('topic', '').strip()
        video.resource_type = request.form.get('resource_type', 'video')
        video.status = request.form.get('status', 'draft')
        db.session.commit()
        flash(f'Resource "{title}" updated successfully!', 'success')
        return redirect(url_for('mentor.videos'))

    return render_template('mentor/video_form.html', courses=courses, video=video)


@mentor_bp.route('/videos/<int:video_id>/toggle-status', methods=['POST'])
@login_required
@mentor_admin_required
def toggle_video_status(video_id):
    from app.models.video import Video
    video = Video.query.get_or_404(video_id)
    video.status = 'published' if video.status == 'draft' else 'draft'
    db.session.commit()
    flash(f'Resource {"published" if video.status == "published" else "moved to draft"}.', 'success')
    return redirect(url_for('mentor.videos'))


@mentor_bp.route('/videos/<int:video_id>/delete', methods=['POST'])
@login_required
@mentor_admin_required
def delete_video(video_id):
    from app.models.video import Video
    video = Video.query.get_or_404(video_id)
    title = video.title
    db.session.delete(video)
    db.session.commit()
    flash(f'Resource "{title}" deleted.', 'info')
    return redirect(url_for('mentor.videos'))


# ─────────────────────────────────────────
# DAILY UPDATES
# ─────────────────────────────────────────
@mentor_bp.route('/updates')
@login_required
@mentor_admin_required
def updates():
    from app.models.update import DailyUpdate
    from app.models.course import Course
    updates_list = DailyUpdate.query.order_by(DailyUpdate.created_at.desc()).all()
    courses      = Course.query.filter_by(status='active').all()
    return render_template('mentor/updates.html', updates=updates_list, courses=courses)


@mentor_bp.route('/updates/create', methods=['POST'])
@login_required
@mentor_admin_required
def create_update():
    from app.models.update import DailyUpdate
    from app.models.announcement import Notification
    from app.models.course import CourseEnrollment
    from app.models.user import User

    title     = request.form.get('title', '').strip()
    content   = request.form.get('content', '').strip()
    course_id = request.form.get('course_id', None, type=int)

    if not title or not content:
        flash('Title and content are required.', 'danger')
        return redirect(url_for('mentor.updates'))

    update = DailyUpdate(
        title=title,
        content=content,
        course_id=course_id,
        created_by=current_user.id
    )
    db.session.add(update)
    db.session.flush()

    # Notify relevant students
    if course_id:
        enrollments = CourseEnrollment.query.filter_by(course_id=course_id, is_active=True).all()
        student_ids = [e.user_id for e in enrollments]
    else:
        students = User.query.filter_by(role='student', is_active=True).all()
        student_ids = [s.id for s in students]

    for uid in student_ids:
        db.session.add(Notification(
            user_id=uid,
            title=f'New Update: {title}',
            content=content[:100],
            type='update',
            related_id=update.id
        ))

    db.session.commit()
    flash(f'Update "{title}" posted successfully!', 'success')
    return redirect(url_for('mentor.updates'))


@mentor_bp.route('/updates/<int:update_id>/delete', methods=['POST'])
@login_required
@mentor_admin_required
def delete_update(update_id):
    from app.models.update import DailyUpdate
    update = DailyUpdate.query.get_or_404(update_id)
    db.session.delete(update)
    db.session.commit()
    flash('Update deleted.', 'info')
    return redirect(url_for('mentor.updates'))


# ─────────────────────────────────────────
# MESSAGES / CHAT
# ─────────────────────────────────────────
@mentor_bp.route('/messages')
@login_required
@mentor_admin_required
def messages():
    from app.models.chat import Conversation, Message
    conversations = Conversation.query.filter_by(
        mentor_id=current_user.id
    ).order_by(
        Conversation.last_message_at.desc()).all()
    for convo in conversations:
        convo.latest_message = convo.messages.order_by(
            Message.created_at.desc(), Message.id.desc()
        ).first()
    return render_template('mentor/messages.html', conversations=conversations)


@mentor_bp.route('/messages/<int:conversation_id>')
@login_required
@mentor_admin_required
def conversation(conversation_id):
    from app.models.chat import Conversation, Message
    from app.models.announcement import Notification
    convo = Conversation.query.filter_by(
        id=conversation_id,
        mentor_id=current_user.id
    ).first_or_404()

    # Mark all student messages as read
    Message.query.filter_by(
        conversation_id=conversation_id,
        sender_id=convo.student_id,
        is_read=False
    ).update({'is_read': True})
    Notification.query.filter_by(
        user_id=current_user.id,
        type='message',
        related_id=convo.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()

    messages_list = convo.messages.order_by(
        Message.created_at.asc(), Message.id.asc()
    ).all()
    return render_template('mentor/conversation.html',
                           convo=convo,
                           messages=messages_list)


@mentor_bp.route('/messages/<int:conversation_id>/send', methods=['POST'])
@login_required
@mentor_admin_required
def send_message(conversation_id):
    from app.models.chat import Conversation, Message
    from app.models.announcement import Notification
    convo = Conversation.query.filter_by(
        id=conversation_id,
        mentor_id=current_user.id
    ).first_or_404()
    content = request.form.get('content', '').strip()

    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('mentor.conversation', conversation_id=conversation_id))

    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=content,
        is_read=False
    )
    db.session.add(msg)
    convo.last_message_at = datetime.utcnow()

    # Notify student
    db.session.add(Notification(
        user_id=convo.student_id,
        title='Your mentor sent you a new message.',
        content=content[:80],
        type='message',
        related_id=convo.id
    ))
    db.session.commit()
    return redirect(url_for('mentor.conversation', conversation_id=conversation_id))


# ─────────────────────────────────────────
# ANNOUNCEMENTS
# ─────────────────────────────────────────
@mentor_bp.route('/announcements')
@login_required
@mentor_admin_required
def announcements():
    from app.models.announcement import Announcement
    from app.models.course import Course
    announcements_list = Announcement.query.order_by(
        Announcement.created_at.desc()).all()
    courses = Course.query.filter_by(status='active').all()
    return render_template('mentor/announcements.html',
                           announcements=announcements_list, courses=courses)


@mentor_bp.route('/announcements/send', methods=['POST'])
@login_required
@mentor_admin_required
def send_announcement():
    from app.models.announcement import Announcement, Notification
    from app.models.course import Course, CourseEnrollment
    from app.models.user import User

    title           = request.form.get('title', '').strip()
    content         = request.form.get('content', '').strip()
    target_type     = request.form.get('target_type', 'all')
    target_course_id = request.form.get('target_course_id', None, type=int)

    if not title or not content:
        flash('Title and content are required.', 'danger')
        return redirect(url_for('mentor.announcements'))

    ann = Announcement(
        title=title,
        content=content,
        target_type=target_type,
        target_course_id=target_course_id if target_type == 'course' else None,
        created_by=current_user.id
    )
    db.session.add(ann)
    db.session.flush()

    # Send notifications
    if target_type == 'course' and target_course_id:
        enrollments = CourseEnrollment.query.filter_by(
            course_id=target_course_id, is_active=True).all()
        student_ids = [e.user_id for e in enrollments]
    else:
        students = User.query.filter_by(role='student', is_active=True).all()
        student_ids = [s.id for s in students]

    for uid in student_ids:
        db.session.add(Notification(
            user_id=uid,
            title=f'Announcement: {title}',
            content=content[:100],
            type='announcement',
            related_id=ann.id
        ))

    db.session.commit()
    flash(f'Announcement sent to {len(student_ids)} student(s)!', 'success')
    return redirect(url_for('mentor.announcements'))


@mentor_bp.route('/announcements/<int:ann_id>/delete', methods=['POST'])
@login_required
@mentor_admin_required
def delete_announcement(ann_id):
    from app.models.announcement import Announcement
    ann = Announcement.query.get_or_404(ann_id)
    db.session.delete(ann)
    db.session.commit()
    flash('Announcement deleted.', 'info')
    return redirect(url_for('mentor.announcements'))

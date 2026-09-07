"""
app/routes/student.py — Student Routes (COMPLETE)
===================================================
All routes here require the user to be authenticated
and have role='student'.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from app.decorators import student_required
from app.extensions import db

student_bp = Blueprint('student', __name__)


def _course_access_denied(course_id):
    """Return the restricted-course response or the standard 403 page."""
    from app.models.course import Course

    course = Course.query.get(course_id)
    if course and course.name == 'Generative AI':
        return render_template('errors/generative_access.html'), 403
    abort(403)


# ─────────────────────────────────────────
# HOME
# ─────────────────────────────────────────
@student_bp.route('/home')
@login_required
@student_required
def home():
    from app.models.quiz import Quiz, QuizAttempt
    from app.models.update import DailyUpdate
    from app.models.chat import Conversation
    from app.models.user import User

    enrolled_courses = current_user.get_enrolled_courses()
    enrolled_ids     = [c.id for c in enrolled_courses]
    completed_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id
    ).filter(QuizAttempt.submitted_at.isnot(None)).all()
    average_quiz_score = round(
        sum(attempt.percentage for attempt in completed_attempts) /
        len(completed_attempts), 1
    ) if completed_attempts else None

    # Recent daily updates for enrolled courses (or global)
    updates = DailyUpdate.query.filter(
        db.or_(
            DailyUpdate.course_id.in_(enrolled_ids),
            DailyUpdate.course_id.is_(None)
        )
    ).order_by(DailyUpdate.created_at.desc()).limit(5).all()

    # Available quizzes (published, for enrolled courses, not yet attempted)
    attempted_ids = [a.quiz_id for a in
                     QuizAttempt.query.filter_by(user_id=current_user.id).all()]
    quizzes = Quiz.query.filter(
        Quiz.course_id.in_(enrolled_ids),
        Quiz.status == 'published',
        Quiz.id.notin_(attempted_ids)
    ).order_by(Quiz.created_at.desc()).limit(5).all()

    # Unread message count
    mentor = User.query.filter_by(role='mentor_admin').first()
    convo = Conversation.query.filter_by(
        student_id=current_user.id,
        mentor_id=mentor.id if mentor else 0
    ).first()
    unread_count = convo.get_unread_count_for_student() if convo else 0

    # Notification count
    unread_notifs = current_user.get_unread_notification_count()

    return render_template('student/home.html',
                           enrolled_courses=enrolled_courses,
                           completed_quizzes=len(completed_attempts),
                           average_quiz_score=average_quiz_score,
                           updates=updates,
                           quizzes=quizzes,
                           unread_count=unread_count,
                           unread_notifs=unread_notifs,
                           now=datetime.utcnow())


# ─────────────────────────────────────────
# COURSES
# ─────────────────────────────────────────
@student_bp.route('/courses')
@login_required
@student_required
def courses():
    enrolled_courses = current_user.get_enrolled_courses()
    return render_template('student/courses.html', courses=enrolled_courses,
                           enrolled_courses=enrolled_courses)


@student_bp.route('/course/<int:course_id>')
@login_required
@student_required
def course_detail(course_id):
    from app.models.course import Course, CourseEnrollment
    from app.models.quiz import Quiz, QuizAttempt
    from app.models.video import Video
    from app.models.update import DailyUpdate

    # Verify enrolled
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        is_active=True
    ).first()
    if not enrollment:
        return _course_access_denied(course_id)

    course  = Course.query.get_or_404(course_id)
    updates = DailyUpdate.query.filter_by(course_id=course_id).order_by(
        DailyUpdate.created_at.desc()).limit(10).all()
    videos  = Video.query.filter_by(course_id=course_id, status='published').order_by(
        Video.day_number.asc(), Video.order_index.asc(), Video.id.asc()).all()
    quizzes = Quiz.query.filter_by(course_id=course_id, status='published').order_by(
        Quiz.day_number.asc(), Quiz.id.asc()).all()

    # Which quizzes has this student already attempted?
    attempted = {a.quiz_id: a for a in
                 QuizAttempt.query.filter_by(user_id=current_user.id).all()}

    return render_template('student/course_detail.html',
                           course=course,
                           videos=videos,
                           quizzes=quizzes,
                           updates=updates,
                           attempted=attempted)


# ─────────────────────────────────────────
# QUIZ TAKING
# ─────────────────────────────────────────
@student_bp.route('/quiz/<int:quiz_id>/start')
@login_required
@student_required
def quiz_start(quiz_id):
    """Show quiz intro page before starting the timer."""
    from app.models.quiz import Quiz, QuizAttempt
    from app.models.course import CourseEnrollment

    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.status != 'published':
        abort(404)

    # Must be enrolled
    enrolled = CourseEnrollment.query.filter_by(
        user_id=current_user.id, course_id=quiz.course_id, is_active=True).first()
    if not enrolled:
        return _course_access_denied(quiz.course_id)

    # Prevent duplicate attempts after a valid submission.
    submitted_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).filter(QuizAttempt.submitted_at.isnot(None)).first()
    if submitted_attempt:
        return redirect(url_for('student.quiz_result', quiz_id=quiz_id))

    return render_template('student/quiz_start.html', quiz=quiz)


@student_bp.route('/quiz/<int:quiz_id>/take')
@login_required
@student_required
def quiz_take(quiz_id):
    """The actual quiz with all questions — no answers shown."""
    from app.models.quiz import Quiz, QuizAttempt, QuizQuestion
    from app.models.course import CourseEnrollment

    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.status != 'published':
        abort(404)

    enrolled = CourseEnrollment.query.filter_by(
        user_id=current_user.id, course_id=quiz.course_id, is_active=True).first()
    if not enrolled:
        return _course_access_denied(quiz.course_id)

    # Create or resume a single in-progress attempt; submitted attempts stay locked.
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).order_by(QuizAttempt.submitted_at.desc().nullslast(), QuizAttempt.id.desc()).first()

    if attempt and attempt.submitted_at:
        flash('You have already submitted this quiz.', 'info')
        return redirect(url_for('student.quiz_result', quiz_id=quiz_id))

    if not attempt:
        attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz_id,
            total_marks=quiz.total_marks,
            started_at=datetime.utcnow()
        )
        db.session.add(attempt)
        db.session.commit()

    questions = quiz.questions.all()
    answers_map = {answer.question_id: answer for answer in attempt.answers.all()}
    return render_template('student/quiz_take.html',
                           quiz=quiz,
                           questions=questions,
                           attempt=attempt,
                           answers_map=answers_map)


@student_bp.route('/quiz/<int:quiz_id>/reset', methods=['POST'])
@login_required
@student_required
def quiz_reset(quiz_id):
    """Delete only the active unfinished attempt; submitted history is retained."""
    from flask import jsonify
    from app.models.course import CourseEnrollment
    from app.models.quiz import Quiz, QuizAttempt

    quiz = Quiz.query.get_or_404(quiz_id)
    enrolled = CourseEnrollment.query.filter_by(
        user_id=current_user.id, course_id=quiz.course_id, is_active=True).first()
    if not enrolled:
        return _course_access_denied(quiz.course_id)
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id, quiz_id=quiz_id, submitted_at=None).first()
    if attempt:
        db.session.delete(attempt)
        db.session.commit()
    return jsonify({'status': 'reset'})


@student_bp.route('/quiz/<int:quiz_id>/answer', methods=['POST'])
@login_required
@student_required
def quiz_answer(quiz_id):
    """Check and persist one answer immediately, without finishing the quiz."""
    from flask import jsonify
    from app.models.course import CourseEnrollment
    from app.models.quiz import Quiz, QuizAttempt, QuizAnswer, QuizQuestion

    quiz = Quiz.query.get_or_404(quiz_id)
    enrolled = CourseEnrollment.query.filter_by(
        user_id=current_user.id, course_id=quiz.course_id, is_active=True).first()
    if quiz.status != 'published':
        abort(403)
    if not enrolled:
        return _course_access_denied(quiz.course_id)

    payload = request.get_json(silent=True) or request.form
    question_id = payload.get('question_id', type=int)
    selected = (payload.get('selected_option') or '').upper()
    if selected not in {'A', 'B', 'C', 'D'}:
        return jsonify({'error': 'Choose one of the four options.'}), 400

    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id, quiz_id=quiz_id, submitted_at=None).first()
    question = QuizQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first_or_404()
    if not attempt or attempt.submitted_at:
        return jsonify({'error': 'This quiz attempt is no longer active.'}), 409

    answer = QuizAnswer.query.filter_by(
        attempt_id=attempt.id, question_id=question.id).first()
    if answer and answer.selected_option:
        selected = answer.selected_option
    else:
        is_correct = selected == question.correct_option
        answer = answer or QuizAnswer(attempt_id=attempt.id, question_id=question.id)
        answer.selected_option = selected
        answer.is_correct = is_correct
        db.session.add(answer)
        db.session.commit()

    return jsonify({
        'selected_option': selected,
        'correct_option': question.correct_option,
        'is_correct': answer.is_correct,
        'explanation': question.explanation,
    })


@student_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
@student_required
def quiz_submit(quiz_id):
    """Process quiz submission — auto-grade and save results."""
    from app.models.course import CourseEnrollment
    from app.models.quiz import Quiz, QuizAttempt, QuizQuestion, QuizAnswer

    quiz    = Quiz.query.get_or_404(quiz_id)
    enrolled = CourseEnrollment.query.filter_by(
        user_id=current_user.id, course_id=quiz.course_id, is_active=True).first()
    if not enrolled:
        return _course_access_denied(quiz.course_id)
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id, quiz_id=quiz_id, submitted_at=None).first()

    if not attempt:
        flash('No active attempt found.', 'danger')
        return redirect(url_for('student.courses'))

    if attempt.submitted_at:
        flash('Quiz already submitted.', 'info')
        return redirect(url_for('student.quiz_result', quiz_id=quiz_id))

    questions = quiz.questions.all()
    for question in questions:
        selected = (request.form.get(f'q_{question.id}', '') or '').upper()
        if selected and selected in {'A', 'B', 'C', 'D'}:
            answer = QuizAnswer.query.filter_by(
                attempt_id=attempt.id, question_id=question.id).first()
            if not answer:
                answer = QuizAnswer(attempt_id=attempt.id, question_id=question.id)
                db.session.add(answer)
            answer.selected_option = selected
            answer.is_correct = selected == question.correct_option

    db.session.flush()
    answers = {answer.question_id: answer for answer in attempt.answers.all()}
    if any(question.id not in answers or not answers[question.id].selected_option for question in questions):
        flash('Answer every question before finishing the quiz.', 'warning')
        return redirect(url_for('student.quiz_take', quiz_id=quiz_id))

    score = sum(question.marks for question in questions
                if answers[question.id].is_correct)
    correct_count = sum(1 for answer in answers.values() if answer.is_correct)
    wrong_count = len(answers) - correct_count
    skipped_count = 0

    total = quiz.calculate_total_marks() or 1
    attempt.score         = score
    attempt.total_marks   = total
    attempt.percentage    = round((score / total) * 100, 1)
    attempt.correct_count = correct_count
    attempt.wrong_count   = wrong_count
    attempt.skipped_count = skipped_count
    attempt.submitted_at  = datetime.utcnow()

    db.session.commit()
    flash(f'Quiz submitted! You scored {score}/{total} ({attempt.percentage}%)', 'success')
    return redirect(url_for('student.quiz_result', quiz_id=quiz_id))


@student_bp.route('/quiz/<int:quiz_id>/result')
@login_required
@student_required
def quiz_result(quiz_id):
    """Show detailed results after quiz submission."""
    from app.models.course import CourseEnrollment
    from app.models.quiz import Quiz, QuizAttempt, QuizAnswer

    quiz    = Quiz.query.get_or_404(quiz_id)
    enrolled = CourseEnrollment.query.filter_by(
        user_id=current_user.id, course_id=quiz.course_id, is_active=True).first()
    if not enrolled:
        return _course_access_denied(quiz.course_id)
    attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id, quiz_id=quiz_id).order_by(
        QuizAttempt.submitted_at.desc().nullslast(), QuizAttempt.id.desc()).first()

    if not attempt or not attempt.submitted_at:
        return redirect(url_for('student.quiz_start', quiz_id=quiz_id))

    # Build a map of question_id -> student's answer
    answers_map = {a.question_id: a for a in attempt.answers.all()}
    questions   = quiz.questions.all()

    return render_template('student/quiz_result.html',
                           quiz=quiz,
                           attempt=attempt,
                           questions=questions,
                           answers_map=answers_map)


# ─────────────────────────────────────────
# PROGRESS
# ─────────────────────────────────────────
@student_bp.route('/progress')
@login_required
@student_required
def progress():
    from app.models.quiz import QuizAttempt

    enrolled_courses = current_user.get_enrolled_courses()
    attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id
    ).filter(
        QuizAttempt.submitted_at.isnot(None)
    ).order_by(QuizAttempt.submitted_at.desc()).all()

    total_score = sum(a.score for a in attempts)
    total_marks = sum(a.total_marks for a in attempts) or 1
    overall_pct = round((total_score / total_marks) * 100, 1)

    return render_template('student/progress.html',
                           enrolled_courses=enrolled_courses,
                           attempts=attempts,
                           overall_pct=overall_pct)


# ─────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────
@student_bp.route('/chat')
@login_required
@student_required
def chat():
    from app.models.chat import Conversation, Message
    from app.models.announcement import Notification
    from app.models.user import User

    mentor = User.query.filter_by(role='mentor_admin').first()
    convo = Conversation.query.filter_by(
        student_id=current_user.id,
        mentor_id=mentor.id if mentor else 0
    ).first()
    messages_list = []

    if convo:
        # Mark mentor messages as read
        Message.query.filter_by(
            conversation_id=convo.id,
            sender_id=mentor.id if mentor else 0,
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

    return render_template('student/chat.html',
                           mentor=mentor,
                           convo=convo,
                           messages=messages_list)


@student_bp.route('/chat/send', methods=['POST'])
@login_required
@student_required
def chat_send():
    from app.models.chat import Conversation, Message
    from app.models.announcement import Notification
    from app.models.user import User

    sender_name = request.form.get('name', '').strip() or current_user.name.strip()
    content = request.form.get('content', '').strip()
    if not content:
        flash('Message cannot be empty.', 'danger')
        return redirect(url_for('student.chat'))

    mentor = User.query.filter_by(role='mentor_admin').first()
    if not mentor:
        flash('Mentor not available.', 'warning')
        return redirect(url_for('student.chat'))

    convo = Conversation.query.filter_by(
        student_id=current_user.id,
        mentor_id=mentor.id
    ).first()

    if not convo:
        convo = Conversation(student_id=current_user.id, mentor_id=mentor.id)
        db.session.add(convo)
        db.session.flush()

    msg = Message(
        conversation_id=convo.id,
        sender_id=current_user.id,
        content=content,
        is_read=False
    )
    db.session.add(msg)
    convo.last_message_at = datetime.utcnow()
    db.session.add(Notification(
        user_id=mentor.id,
        title=f'{current_user.name} sent you a new message.',
        content=content[:80],
        type='message',
        related_id=convo.id
    ))
    db.session.commit()

    return redirect(url_for('student.chat'))


# ─────────────────────────────────────────
# PROFILE & ACCOUNT
# ─────────────────────────────────────────
@student_bp.route('/profile')
@login_required
@student_required
def profile():
    from app.models.quiz import QuizAttempt
    attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id
    ).filter(QuizAttempt.submitted_at.isnot(None)).all()

    best_pct = max((a.percentage for a in attempts), default=0)
    return render_template('student/profile.html',
                           attempts=attempts,
                           best_pct=best_pct)


@student_bp.route('/account', methods=['GET', 'POST'])
@login_required
@student_required
def account():
    from werkzeug.security import check_password_hash, generate_password_hash

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_name':
            name = request.form.get('name', '').strip()
            if len(name) < 2:
                flash('Name must be at least 2 characters.', 'danger')
            else:
                current_user.name = name
                db.session.commit()
                flash('Name updated successfully!', 'success')

        elif action == 'change_password':
            current_pw  = request.form.get('current_password', '')
            new_pw      = request.form.get('new_password', '')
            confirm_pw  = request.form.get('confirm_password', '')

            if not check_password_hash(current_user.password_hash, current_pw):
                flash('Current password is incorrect.', 'danger')
            elif len(new_pw) < 8:
                flash('New password must be at least 8 characters.', 'danger')
            elif new_pw != confirm_pw:
                flash('Passwords do not match.', 'danger')
            else:
                current_user.password_hash = generate_password_hash(new_pw)
                db.session.commit()
                flash('Password changed successfully!', 'success')

        return redirect(url_for('student.account'))

    return render_template('student/account.html')


# ─────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────
@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    from app.models.announcement import Notification
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()

    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()

    return render_template('student/notifications.html', notifications=notifs)

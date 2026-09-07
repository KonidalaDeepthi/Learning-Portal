"""
app/models/quiz.py — Quiz, Question, Attempt, Answer Models
=============================================================
Four related models:

1. Quiz        — the quiz itself (title, course, time limit)
2. QuizQuestion — each question inside a quiz
3. QuizAttempt  — records when a student takes a quiz (score stored here)
4. QuizAnswer   — records the student's answer to each question
"""

from datetime import datetime
from app.extensions import db


class Quiz(db.Model):
    """A quiz created by the MENTOR_ADMIN for a specific course."""

    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    day_number = db.Column(db.Integer, nullable=True)

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    # ^ Every quiz belongs to one course. Students can only see quizzes
    # for courses they are enrolled in.

    time_limit_minutes = db.Column(db.Integer, default=0, nullable=False)
    # ^ 0 = no time limit. Otherwise, countdown timer in frontend.

    total_marks = db.Column(db.Integer, default=0, nullable=False)
    # ^ Auto-calculated from sum of question marks, or set manually.

    status = db.Column(db.String(20), default='draft', nullable=False)
    # ^ 'draft' (only mentor sees) or 'published' (students can attempt)

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # Relationships
    course = db.relationship('Course', back_populates='quizzes')
    questions = db.relationship('QuizQuestion', back_populates='quiz',
                                lazy='dynamic', cascade='all, delete-orphan',
                                order_by='QuizQuestion.order_index')
    attempts = db.relationship('QuizAttempt', back_populates='quiz',
                               lazy='dynamic', cascade='all, delete-orphan')

    def get_question_count(self):
        return self.questions.count()

    def calculate_total_marks(self):
        """Sum up marks from all questions."""
        return sum(q.marks for q in self.questions.all())

    def __repr__(self):
        return f'<Quiz {self.title}>'


class QuizQuestion(db.Model):
    """A single question inside a quiz, with 4 options."""

    __tablename__ = 'quiz_questions'

    id = db.Column(db.Integer, primary_key=True)

    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)

    question_text = db.Column(db.Text, nullable=False)
    # ^ The actual question text

    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)

    correct_option = db.Column(db.String(1), nullable=False)
    # ^ Must be 'A', 'B', 'C', or 'D'. Never shown to students during attempt.

    explanation = db.Column(db.Text, nullable=False, default='')
    # ^ Beginner-friendly explanation shown immediately after an answer.

    marks = db.Column(db.Integer, default=1, nullable=False)
    # ^ How many marks this question is worth

    order_index = db.Column(db.Integer, default=0, nullable=False)
    # ^ Controls display order of questions

    # Relationships
    quiz = db.relationship('Quiz', back_populates='questions')
    answers = db.relationship('QuizAnswer', back_populates='question',
                              lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Question {self.id} for Quiz {self.quiz_id}>'


class QuizAttempt(db.Model):
    """
    Records when a student attempts a quiz.
    One row = one attempt by one student on one quiz.
    
    UNIQUE CONSTRAINT: (user_id, quiz_id)
    A student can only attempt each quiz ONCE.
    """

    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)

    score = db.Column(db.Integer, default=0, nullable=False)
    # ^ How many marks the student earned

    total_marks = db.Column(db.Integer, default=0, nullable=False)
    # ^ Copy of the quiz's total marks at time of attempt
    # (quiz marks might change later, so we preserve the original)

    percentage = db.Column(db.Float, default=0.0, nullable=False)
    # ^ score / total_marks * 100 — calculated on submission

    correct_count = db.Column(db.Integer, default=0, nullable=False)
    wrong_count = db.Column(db.Integer, default=0, nullable=False)
    skipped_count = db.Column(db.Integer, default=0, nullable=False)

    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    # ^ If None, the attempt was started but not submitted yet.

    # Relationships
    user = db.relationship('User', back_populates='quiz_attempts')
    quiz = db.relationship('Quiz', back_populates='attempts')
    answers = db.relationship('QuizAnswer', back_populates='attempt',
                              lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Attempt user={self.user_id} quiz={self.quiz_id} score={self.score}>'


class QuizAnswer(db.Model):
    """
    Records a student's answer to a single question within an attempt.
    One QuizAttempt has many QuizAnswers (one per question).
    """

    __tablename__ = 'quiz_answers'

    id = db.Column(db.Integer, primary_key=True)

    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)

    selected_option = db.Column(db.String(1), nullable=True)
    # ^ 'A', 'B', 'C', 'D', or None if question was skipped

    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    # ^ Evaluated at submission time (selected_option == question.correct_option)

    answered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    attempt = db.relationship('QuizAttempt', back_populates='answers')
    question = db.relationship('QuizQuestion', back_populates='answers')

    def __repr__(self):
        return f'<Answer attempt={self.attempt_id} question={self.question_id} correct={self.is_correct}>'

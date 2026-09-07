"""
app/models/chat.py — Conversation and Message Models
"""
from datetime import datetime
from app.extensions import db


class Conversation(db.Model):
    """
    A private conversation thread between one student and the mentor.
    
    Each student has exactly ONE conversation with the mentor.
    (Enforced by unique constraint on student_id + mentor_id)
    """
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # ^ Always the MENTOR_ADMIN's user.id

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    # ^ Optional course context for course-specific conversations

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = db.Column(db.DateTime, nullable=True)
    # ^ Updated when a new message is sent — used to sort conversations

    # Unique: only one conversation per student-mentor pair
    __table_args__ = (
        db.UniqueConstraint('student_id', 'mentor_id', name='uq_student_mentor_convo'),
    )

    # Relationships
    student = db.relationship('User', foreign_keys=[student_id],
                              back_populates='student_conversations')
    mentor = db.relationship('User', foreign_keys=[mentor_id])
    messages = db.relationship('Message', back_populates='conversation',
                               lazy='dynamic', cascade='all, delete-orphan',
                               order_by='Message.created_at')

    def get_unread_count_for_mentor(self):
        """How many unread messages from the student?"""
        return self.messages.filter_by(
            sender_id=self.student_id,
            is_read=False
        ).count()

    def get_unread_count_for_student(self):
        """How many unread messages from the mentor?"""
        return self.messages.filter_by(
            sender_id=self.mentor_id,
            is_read=False
        ).count()

    def __repr__(self):
        return f'<Conversation student={self.student_id} mentor={self.mentor_id}>'


class Message(db.Model):
    """
    A single message inside a Conversation.
    sender_id tells us who sent it (student or mentor).
    """
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)

    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # ^ Can be the student or the mentor

    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = db.relationship('Conversation', back_populates='messages')
    sender = db.relationship('User', foreign_keys=[sender_id])

    def __repr__(self):
        return f'<Message from={self.sender_id} read={self.is_read}>'

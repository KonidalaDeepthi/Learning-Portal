"""
app/models/video.py — Learning Resource / Video Model
"""
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from app.extensions import db


class Video(db.Model):
    """
    A learning resource (video, article, document) linked to a course.
    Stores the URL (YouTube, Google Drive, etc.) — not the actual file.
    """
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(500), nullable=False)
    # ^ YouTube URL, Google Drive link, etc.
    thumbnail_url = db.Column(db.String(500), nullable=True)
    # ^ Optional preview image URL

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    topic = db.Column(db.String(100), nullable=True)
    # ^ e.g., "Flask Basics", "Prompt Engineering"

    resource_type = db.Column(db.String(50), default='video', nullable=False)
    # ^ 'video', 'article', 'document', 'assignment'

    status = db.Column(db.String(20), default='draft', nullable=False)
    # ^ 'draft' or 'published'

    order_index = db.Column(db.Integer, default=0)
    # ^ Controls display order within a course

    day_number = db.Column(db.Integer, nullable=True)
    # ^ Optional course day used to order structured learning content

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # Relationships
    course = db.relationship('Course', back_populates='videos')

    @property
    def watch_url(self):
        """Return a standard YouTube watch URL when the resource is a YouTube link."""
        parsed = urlparse(self.url)
        host = parsed.netloc.lower().removeprefix('www.')
        if host == 'youtu.be':
            video_id = parsed.path.strip('/')
            return f'https://www.youtube.com/watch?v={video_id}' if video_id else self.url
        if host == 'youtube.com' and parsed.path.startswith('/embed/'):
            video_id = parsed.path.removeprefix('/embed/').strip('/')
            return f'https://www.youtube.com/watch?v={video_id}' if video_id else self.url
        if host == 'youtube.com' and parse_qs(parsed.query).get('v'):
            return self.url
        return self.url

    def __repr__(self):
        return f'<Video {self.title}>'

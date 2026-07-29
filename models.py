from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


# =====================================================
# USER
# =====================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    progress = db.relationship(
        "Progress",
        backref="user",
        lazy=True,
        cascade="all, delete"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =====================================================
# COURSE
# =====================================================

class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text)

    image = db.Column(
        db.String(255),
        default="default_course.png"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    lessons = db.relationship(
        "Lesson",
        backref="course",
        lazy=True,
        cascade="all, delete"
    )


# =====================================================
# LESSON
# =====================================================

class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    summary = db.Column(db.Text)

    lesson_number = db.Column(db.Integer)

    video_filename = db.Column(db.String(255))

    notes_filename = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    quizzes = db.relationship(
        "Quiz",
        backref="lesson",
        lazy=True,
        cascade="all, delete"
    )

    videos = db.relationship(
        "Video",
        backref="lesson",
        lazy=True,
        cascade="all, delete"
    )

    notes = db.relationship(
        "Note",
        backref="lesson",
        lazy=True,
        cascade="all, delete"
    )

    progress_records = db.relationship(
        "Progress",
        backref="lesson",
        lazy=True,
        cascade="all, delete"
    )


# =====================================================
# QUIZ
# =====================================================

class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)

    question = db.Column(db.Text, nullable=False)

    option1 = db.Column(db.String(255))

    option2 = db.Column(db.String(255))

    option3 = db.Column(db.String(255))

    option4 = db.Column(db.String(255))

    answer = db.Column(db.String(1))

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id"),
        nullable=False
    )


# =====================================================
# VIDEO
# =====================================================

class Video(db.Model):
    __tablename__ = "videos"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    filename = db.Column(db.String(255))

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id"),
        nullable=False
    )


# =====================================================
# NOTES
# =====================================================

class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    filename = db.Column(db.String(255), nullable=False)

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id"),
        nullable=False
    )


# =====================================================
# PROGRESS
# =====================================================

class Progress(db.Model):
    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)

    completed = db.Column(
        db.Boolean,
        default=False
    )

    percentage = db.Column(
        db.Integer,
        default=0
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id"),
        nullable=False
    )
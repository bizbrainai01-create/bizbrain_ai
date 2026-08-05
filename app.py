from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.utils import secure_filename

from dotenv import load_dotenv

import os

from extensions import db
from models import (
    User,
    Course,
    Lesson,
    Progress,
    Quiz,
    Note,
    Video
)

from ai import ask_ai


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()


# ==========================================
# CREATE APP
# ==========================================

app = Flask(__name__)


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "bizbrain-secret"
)

import os

database_url = os.getenv("DATABASE_URL")

if database_url:
    # Render PostgreSQL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

else:
    # Local SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bizbrain.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload folders
app.config["VIDEO_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "videos"
)

app.config["NOTES_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "notes"
)

os.makedirs(app.config["VIDEO_FOLDER"], exist_ok=True)
os.makedirs(app.config["NOTES_FOLDER"], exist_ok=True)
import os
from werkzeug.utils import secure_filename
# Maximum upload size (500 MB)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
ALLOWED_VIDEO_EXTENSIONS = {"mp4"}
ALLOWED_NOTE_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx"}

def allowed_video(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_note(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_NOTE_EXTENSIONS

# Upload folders for lesson uploads
app.config["UPLOAD_VIDEO_FOLDER"] = app.config["VIDEO_FOLDER"]
app.config["UPLOAD_NOTE_FOLDER"] = app.config["NOTES_FOLDER"]

# Create folders automatically if they don't exist
os.makedirs(app.config["VIDEO_FOLDER"], exist_ok=True)
os.makedirs(app.config["NOTES_FOLDER"], exist_ok=True)

# ==========================================
# INITIALIZE DATABASE
# ==========================================

db.init_app(app)


# ==========================================
# LOGIN MANAGER
# ==========================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = "Please login first."


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# REGISTER
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:

        if current_user.is_admin:
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form["name"].strip()

        email = request.form["email"].lower().strip()

        password = request.form["password"]

        confirm = request.form["confirm_password"]

        if password != confirm:

            flash("Passwords do not match.", "danger")

            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():

            flash("Email already exists.", "warning")

            return redirect(url_for("register"))

        user = User(

            name=name,

            email=email,

            is_admin=False

        )

        user.set_password(password)

        db.session.add(user)

        db.session.commit()

        login_user(user)

        flash("Welcome to BizBrain AI!", "success")

        return redirect(url_for("dashboard"))

    return render_template("register.html")


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        if current_user.is_admin:
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form["email"].lower()

        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user:

            flash("Invalid email.", "danger")

            return redirect(url_for("login"))

        if not user.check_password(password):

            flash("Incorrect password.", "danger")

            return redirect(url_for("login"))

        login_user(user)

        flash("Login successful.", "success")

        if user.is_admin:

            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("home"))

from werkzeug.utils import secure_filename

from uuid import uuid4

@app.route("/admin/lesson/add", methods=["GET", "POST"])
@login_required
def add_lesson():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    courses = Course.query.order_by(Course.title).all()

    if request.method == "POST":

        title = request.form["title"].strip()
        summary = request.form.get("summary", "").strip()
        lesson_number = int(request.form["lesson_number"])
        course_id = int(request.form["course_id"])

        video = request.files.get("video")
        notes = request.files.get("notes")

        video_filename = None
        notes_filename = None

        # ==========================
        # Upload Video
        # ==========================

        if video and video.filename:

            if not allowed_video(video.filename):
                flash("Only MP4 videos are allowed.", "danger")
                return redirect(request.url)

            video_filename = (
                f"{uuid4().hex}_{secure_filename(video.filename)}"
            )

            video.save(
                os.path.join(
                    app.config["VIDEO_FOLDER"],
                    video_filename
                )
            )

        # ==========================
        # Upload Notes
        # ==========================

        if notes and notes.filename:

            if not allowed_note(notes.filename):
                flash("Invalid notes file.", "danger")
                return redirect(request.url)

            notes_filename = (
                f"{uuid4().hex}_{secure_filename(notes.filename)}"
            )

            notes.save(
                os.path.join(
                    app.config["NOTES_FOLDER"],
                    notes_filename
                )
            )

        # ==========================
        # Save Lesson
        # ==========================

        lesson = Lesson(
            title=title,
            summary=summary,
            lesson_number=lesson_number,
            course_id=course_id,
            video_filename=video_filename,
            notes_filename=notes_filename
        )

        db.session.add(lesson)
        db.session.commit()

        flash("Lesson uploaded successfully.", "success")

        return redirect(url_for("admin_lessons"))

    return render_template(
        "admin/add_lesson.html",
        courses=courses
    )
@app.route("/admin/lesson/edit/<int:lesson_id>", methods=["GET", "POST"])
@login_required
def edit_lesson(lesson_id):

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lesson = Lesson.query.get_or_404(lesson_id)
    courses = Course.query.order_by(Course.title).all()

    if request.method == "POST":

        lesson.title = request.form["title"]
        lesson.summary = request.form["summary"]
        lesson.lesson_number = int(request.form["lesson_number"])
        lesson.course_id = int(request.form["course_id"])

        db.session.commit()

        flash("Lesson updated successfully.", "success")

        return redirect(url_for("admin_lessons"))

    return render_template(
        "admin/edit_lesson.html",
        lesson=lesson,
        courses=courses
    )

@app.route("/admin/lesson/delete/<int:lesson_id>")
@login_required
def delete_lesson(lesson_id):

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lesson = Lesson.query.get_or_404(lesson_id)

    db.session.delete(lesson)

    db.session.commit()

    flash("Lesson deleted.", "success")

    return redirect(url_for("admin_lessons"))

@app.route("/admin/video/<int:lesson_id>/upload", methods=["POST"])
@login_required
def upload_video(lesson_id):

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lesson = Lesson.query.get_or_404(lesson_id)

    video = request.files.get("video")

    if video and video.filename:

        filename = secure_filename(video.filename)

        video.save(
            os.path.join(
                app.config["VIDEO_FOLDER"],
                filename
            )
        )

        lesson.video_filename = filename

        db.session.commit()

        flash("Video uploaded successfully!", "success")

    return redirect(url_for("admin_videos"))

# ==========================================
# STUDENT DASHBOARD
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():

    total_courses = Course.query.count()

    total_lessons = Lesson.query.count()

    total_notes = Lesson.query.filter(
    Lesson.notes_filename.isnot(None)
).count()

    total_videos = Lesson.query.filter(
    Lesson.video_filename.isnot(None)
).count()

    return render_template(
        "dashboard.html",
        total_courses=total_courses,
        total_lessons=total_lessons,
        total_notes=total_notes,
        total_videos=total_videos
    )
# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin")
@login_required
def admin_dashboard():

    if not current_user.is_admin:

        flash("Access denied.", "danger")

        return redirect(url_for("dashboard"))

    return render_template(
        "admin/dashboard.html",
        total_users=User.query.count(),
        total_courses=Course.query.count(),
        total_lessons=Lesson.query.count(),
        total_videos=Lesson.query.filter(
    Lesson.video_filename.isnot(None)
).count()
    )


# ==========================================
# ALL COURSES
# ==========================================

@app.route("/courses")
@login_required
def courses():

    courses = Course.query.order_by(Course.title).all()

    return render_template(
        "courses.html",
        courses=courses
    )


# ==========================================
# SINGLE COURSE
# ==========================================

@app.route("/course/<int:course_id>")
@login_required
def course(course_id):

    course = Course.query.get_or_404(course_id)

    lessons = Lesson.query.filter_by(
        course_id=course.id
    ).order_by(
        Lesson.lesson_number
    ).all()

    return render_template(
        "course.html",
        course=course,
        lessons=lessons
    )

# ==========================
# SMART NOTES
# ==========================

@app.route("/notes")
@login_required
def notes():
    lessons = Lesson.query.filter(
        Lesson.notes_filename.isnot(None)
    ).all()

    return render_template(
        "notes.html",
        lessons=lessons
    )


# ==========================
# VIDEOS
# ==========================

@app.route("/videos")
@login_required
def videos():
    lessons = Lesson.query.filter(
        Lesson.video_filename.isnot(None)
    ).all()

    return render_template(
        "videos.html",
        lessons=lessons
    )


# ==========================
# AI TUTOR
# ==========================

@app.route("/ai-tutor", methods=["GET", "POST"])
@login_required
def ai_tutor():

    answer = ""

    if request.method == "POST":

        question = request.form.get("question")

        if question:

            try:
                answer = ask_ai(question)

            except Exception as e:
                answer = f"Error: {e}"

    return render_template(
        "ai_tutor.html",
        answer=answer
    )

# ==========================
# CERTIFICATES
# ==========================

@app.route("/certificates")
@login_required
def certificates():
    return render_template("certificates.html")

# ==========================================
# SINGLE LESSON
# ==========================================


@app.route("/lesson/<int:lesson_id>")
@login_required
def lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)

    completed = Progress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson.id
    ).first()

    return render_template(
        "lesson.html",
        lesson=lesson,
        completed=completed
    )

@app.route("/ask-ai", methods=["POST"])
@login_required
def ask_ai_route():

    data = request.get_json()

    question = data.get("question")

    answer = ask_ai(question)

    return jsonify({
        "answer": answer
    })

# ==========================================
# MARK LESSON COMPLETE
# ==========================================

@app.route("/complete/<int:lesson_id>")
@login_required
def complete_lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)

    existing = Progress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson.id
    ).first()

    if existing is None:

        progress = Progress(
            user_id=current_user.id,
            lesson_id=lesson.id,
            completed=True,
            score=100
        )

        db.session.add(progress)

        db.session.commit()

        flash("Lesson completed!", "success")

    return redirect(
        url_for(
            "lesson",
            lesson_id=lesson.id
        )
    )


@app.route("/admin/courses")
@login_required
def admin_courses():

    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    courses = Course.query.order_by(Course.id).all()

    return render_template(
        "admin/courses.html",
        courses=courses
    )

@app.route("/admin/course/add", methods=["GET", "POST"])
@login_required
def add_course():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        course = Course(
            title=request.form["title"],
            description=request.form["description"]
        )

        db.session.add(course)
        db.session.commit()

        flash("Course added successfully.", "success")

        return redirect(url_for("admin_courses"))

    return render_template("admin/add_course.html")

@app.route("/admin/course/delete/<int:course_id>")
@login_required
def delete_course(course_id):

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    course = Course.query.get_or_404(course_id)

    db.session.delete(course)

    db.session.commit()

    flash("Course deleted.", "success")

    return redirect(url_for("admin_courses"))


@app.route("/admin/course/edit/<int:course_id>", methods=["GET", "POST"])
@login_required
def edit_course(course_id):

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    course = Course.query.get_or_404(course_id)

    if request.method == "POST":

        course.title = request.form["title"]
        course.description = request.form["description"]

        db.session.commit()

        flash("Course updated.", "success")

        return redirect(url_for("admin_courses"))

    return render_template(
        "admin/edit_course.html",
        course=course
    )

@app.route("/admin/lessons")
@login_required
def admin_lessons():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lessons = Lesson.query.order_by(Lesson.lesson_number).all()

    return render_template(
        "admin/lessons.html",
        lessons=lessons
    )


@app.route("/admin/users")
@login_required
def admin_users():
    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    users = User.query.order_by(User.name).all()

    return render_template(
        "admin/users.html",
        users=users
    )


@app.route("/admin/uploads")
@login_required
def admin_uploads():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lessons = Lesson.query.all()

    return render_template(
        "admin/uploads.html",
        lessons=lessons
    )


@app.route("/admin/upload/note", methods=["POST"])
@login_required
def upload_note():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    file = request.files["note"]

    lesson_id = request.form["lesson_id"]

    if file:

        filename = secure_filename(file.filename)

        file.save(
            os.path.join(
                app.config["UPLOAD_NOTE_FOLDER"],
                filename
            )
        )

        lesson = Lesson.query.get(lesson_id)

        lesson.notes_filename = filename

        db.session.commit()

        flash("Notes uploaded successfully.", "success")

    return redirect(url_for("admin_uploads"))

# ===========================
# ADMIN VIDEOS
# ===========================

@app.route("/admin/videos")
@login_required
def admin_videos():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lessons = Lesson.query.order_by(
        Lesson.lesson_number
    ).all()

    return render_template(
        "admin/videos.html",
        lessons=lessons,
        page_title="Video Management",
    )

@app.route("/admin/notes/<int:lesson_id>/upload", methods=["POST"])
@login_required
def upload_notes(lesson_id):

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lesson = Lesson.query.get_or_404(lesson_id)

    pdf = request.files.get("notes")

    if pdf and pdf.filename.endswith(".pdf"):

        filename = secure_filename(pdf.filename)

        pdf.save(
            os.path.join(
                app.config["NOTES_FOLDER"],
                filename
            )
        )

        lesson.notes_filename = filename

        db.session.commit()

        flash("Notes uploaded successfully!", "success")

    return redirect(url_for("admin_notes"))


@app.route("/admin/video/<int:lesson_id>/delete")
@login_required
def delete_video(lesson_id):

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lesson = Lesson.query.get_or_404(lesson_id)

    if lesson.video_filename:

        filepath = os.path.join(
            app.config["VIDEO_FOLDER"],
            lesson.video_filename
        )

        if os.path.exists(filepath):
            os.remove(filepath)

        lesson.video_filename = None

        db.session.commit()

        flash("Video deleted successfully.", "success")

    return redirect(url_for("admin_videos"))


# ===========================
# ADMIN NOTES
# ===========================

@app.route("/admin/notes")
@login_required
def admin_notes():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    lessons = Lesson.query.all()

    return render_template(
        "admin/notes.html",
        lessons=lessons
    )


# ===========================
# ADMIN QUIZZES
# ===========================

@app.route("/admin/quizzes")
@login_required
def admin_quizzes():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    quizzes = Quiz.query.all()

    return render_template(
        "admin/quizzes.html",
        quizzes=quizzes
    )


# ===========================
# ADMIN STUDENTS
# ===========================

@app.route("/admin/students")
@login_required
def admin_students():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    students = User.query.filter_by(is_admin=False).all()

    return render_template(
        "admin/students.html",
        students=students
    )


# ===========================
# ADMIN CERTIFICATES
# ===========================

@app.route("/admin/certificates")
@login_required
def admin_certificates():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    return render_template("admin/certificates.html")


# ===========================
# ADMIN SETTINGS
# ===========================

@app.route("/admin/settings")
@login_required
def admin_settings():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    return render_template("admin/settings.html")
with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email="bizbrainai01@gmail.com").first()

    if not admin:
        admin = User(
            name="BizBrain Admin",
            email="bizbrainai01@gmail.com",
            is_admin=True
        )

        admin.set_password("Admin@123")

        db.session.add(admin)
        db.session.commit()

        print("✅ Admin created")
if __name__ == "__main__":
    app.run(debug=True)
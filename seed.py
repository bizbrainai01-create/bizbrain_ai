from app import app
from extensions import db
from models import User, Course, Lesson, Quiz

# ==========================================
# CREATE DATABASE
# ==========================================

with app.app_context():

    db.create_all()

    # ==========================================
    # ADMIN ACCOUNT
    # ==========================================

    admin = User.query.filter_by(
        email="bizbrainai01@gmail.com"
    ).first()

    if not admin:

        admin = User(
            name="BizBrain Admin",
            email="bizbrainai01@gmail.com",
            is_admin=True
        )

        admin.set_password("Admin@123")

        db.session.add(admin)

        print("✓ Admin account created.")

    else:

        print("✓ Admin already exists.")

    # ==========================================
    # COURSES
    # ==========================================

    courses = [

        {
            "title": "Principles of Marketing",
            "description": "Learn the foundations of modern marketing."
        },

        {
            "title": "Strategic Brand Management",
            "description": "Build powerful brands."
        },

        {
            "title": "Design Thinking",
            "description": "Solve business problems creatively."
        },

        {
            "title": "Entrepreneur Finance",
            "description": "Understand startup and business finance."
        },

        {
            "title": "Business Law",
            "description": "Legal principles for businesses."
        },

        {
            "title": "Organisational Behaviour",
            "description": "People, leadership and workplace behaviour."
        }

    ]

    for course_data in courses:

        course = Course.query.filter_by(
            title=course_data["title"]
        ).first()

        if not course:

            course = Course(

                title=course_data["title"],

                description=course_data["description"]

            )

            db.session.add(course)

            db.session.flush()

            print(f"✓ Created course: {course.title}")

        # ==========================================
        # LESSONS
        # ==========================================

        for i in range(1, 11):

            lesson = Lesson.query.filter_by(

                title=f"Lesson {i}: {course.title}",

                course_id=course.id

            ).first()

            if not lesson:

                lesson = Lesson(

                    title=f"Lesson {i}: {course.title}",

                    summary=f"This lesson introduces concept {i} of {course.title}.",

                    lesson_number=i,

                    course_id=course.id,

                    video_filename="",

                    notes_filename=""

                )

                db.session.add(lesson)

                db.session.flush()

                print(f"   ✓ Lesson {i}")

                # ==========================================
                # QUIZ
                # ==========================================

                quiz = Quiz(

                    question=f"What is covered in Lesson {i}?",

                    option1="Option A",

                    option2="Option B",

                    option3="Option C",

                    option4="Option D",

                    answer="A",

                    lesson_id=lesson.id

                )

                db.session.add(quiz)

    db.session.commit()

    print("\n===================================")
    print("BizBrain AI database seeded.")
    print("===================================")

    print("\nAdmin Login")

    print("Email: bizbrainai01@gmail.com")

    print("Password: Admin@123")
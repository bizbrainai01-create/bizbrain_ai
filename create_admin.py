from app import app
from extensions import db
from models import User

with app.app_context():

    admin = User.query.filter_by(
        email="bizbrainai01@gmail.com"
    ).first()

    if admin:
        print("Admin already exists.")
    else:
        admin = User(
            name="BizBrain Admin",
            email="bizbrainai01@gmail.com",
            is_admin=True
        )

        admin.set_password("Admin@123")

        db.session.add(admin)
        db.session.commit()

        print("Admin account created successfully!")
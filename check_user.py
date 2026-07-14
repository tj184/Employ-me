# check_user.py
import os
from flask import Flask
from config import Config
from models import db, User, JobSeekerProfile, EmployerProfile

# Create a minimal Flask app just to access the database
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    user = User.query.filter_by(email='tanishjain184@gmail.com').first()

    if not user:
        print('No user found with that email.')
    else:
        print(f"User ID: {user.id}")
        print(f"Name:   {user.name}")
        print(f"Role:   {user.role}")
        print(f"Email:  {user.email}")
        print(f"Created: {user.created_at}")
        print('-' * 40)

        if user.role == 'jobseeker':
            profile = JobSeekerProfile.query.filter_by(user_id=user.id).first()
            if profile:
                print("JobSeeker Profile:")
                for col in profile.__table__.columns:
                    val = getattr(profile, col.name)
                    if col.name not in ('profile_pic', 'aadhar_card'):
                        print(f"  {col.name}: {val}")
            else:
                print("No JobSeekerProfile yet.")
        elif user.role == 'employer':
            profile = EmployerProfile.query.filter_by(user_id=user.id).first()
            if profile:
                print("Employer Profile:")
                for col in profile.__table__.columns:
                    val = getattr(profile, col.name)
                    if col.name != 'profile_pic':
                        print(f"  {col.name}: {val}")
            else:
                print("No EmployerProfile yet.")
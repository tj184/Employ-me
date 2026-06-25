from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'jobseeker' or 'employer'
    name = db.Column(db.String(100), nullable=False)  # kept for simple display
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship
    profile = db.relationship('JobSeekerProfile', backref='user', uselist=False)

class JobSeekerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    # Name parts
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)   # optional
    last_name = db.Column(db.String(50), nullable=False)

    # Personal
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)        # Male, Female, Other
    address = db.Column(db.String(300), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    father_husband_name = db.Column(db.String(100), nullable=False)

    # Education
    education_level = db.Column(db.String(20), nullable=False)  # Post Graduate, Graduate, 12th, 10th, Others
    education_other = db.Column(db.String(100), nullable=True)  # if Others selected

    # Work preferences
    preferred_location1 = db.Column(db.String(100), nullable=False)  # mandatory
    preferred_location2 = db.Column(db.String(100), nullable=True)
    preferred_location3 = db.Column(db.String(100), nullable=True)
    employment_type = db.Column(db.String(20), nullable=False)       # Full-time, Part-time, Both

    # Skills (comma-separated)
    skills = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=False)   # mandatory
    state = db.Column(db.String(100), nullable=False)  # mandatory

    # Images
    profile_pic = db.Column(db.String(200))   # public
    aadhar_card = db.Column(db.String(200))   # private, hidden from employers

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
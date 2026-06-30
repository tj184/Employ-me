from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'jobseeker' or 'employer'
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships – cascade deletes the profile when user is deleted
    profile = db.relationship('JobSeekerProfile', backref='user', uselist=False,
                              cascade='all, delete-orphan')
    employer_profile = db.relationship('EmployerProfile', backref='user', uselist=False,
                                       cascade='all, delete-orphan')


class JobSeekerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    # Name parts
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=False)

    # Personal
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    father_husband_name = db.Column(db.String(100), nullable=False)

    # Education
    education_level = db.Column(db.String(20), nullable=False)
    education_other = db.Column(db.String(100), nullable=True)

    # Work preferences
    preferred_location1 = db.Column(db.String(100), nullable=False)
    preferred_location2 = db.Column(db.String(100), nullable=True)
    preferred_location3 = db.Column(db.String(100), nullable=True)
    employment_type = db.Column(db.String(20), nullable=False)

    # Skills
    skills = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)

    # Images
    profile_pic = db.Column(db.String(200))
    aadhar_card = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False, nullable=False)


class EmployerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    business_name = db.Column(db.String(150), nullable=False)
    business_address = db.Column(db.String(300), nullable=False)
    gst_number = db.Column(db.String(30), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    contact_person_name = db.Column(db.String(100), nullable=False)
    contact_person_phone = db.Column(db.String(15), nullable=False)

    # New location fields
    city = db.Column(db.String(100), nullable=False, default='')
    state = db.Column(db.String(100), nullable=False, default='')
    pincode = db.Column(db.String(10), nullable=False, default='')

    # For identity verification (account deletion)
    dob = db.Column(db.Date, nullable=False, default=date.today)

    # Verified by admin (employer cannot change this)
    verified = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
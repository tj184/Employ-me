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
    # Images
    profile_pic = db.Column(db.String(200))   # business profile picture

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profile.id'), nullable=False)

    employer_name = db.Column(db.String(100), nullable=False)
    employer_address = db.Column(db.String(300), nullable=False)
    employer_mobile = db.Column(db.String(15), nullable=False)
    employer_city = db.Column(db.String(100), nullable=False)
    employer_state = db.Column(db.String(100), nullable=False)
    employer_pincode = db.Column(db.String(10), nullable=False)

    job_name = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    committed_salary = db.Column(db.String(100))
    location = db.Column(db.String(200))
    vacancies = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='Open')
    deleted = db.Column(db.Boolean, default=False, nullable=False)   # <-- new column

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employer = db.relationship('EmployerProfile', backref='jobs')
    # No cascade – applications stay alive even when job is soft‑deleted
    applications = db.relationship('JobApplication', backref='job')

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Do NOT define a `job` relationship here – the backref from Job will create it.
    applicant = db.relationship('User', backref='job_applications')
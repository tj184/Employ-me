import os
import sys
from datetime import date, datetime
from werkzeug.security import generate_password_hash
from config import Config
from models import db, User, JobSeekerProfile, EmployerProfile, Job, JobApplication
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def seed():
    with app.app_context():
        # ---- Reset everything for a clean test ----
        db.drop_all()
        db.create_all()

        # ========================================================
        # 1. Jobseeker – verified & paid
        # ========================================================
        js_user = User(
            email="kavya@example.com",
            password_hash=generate_password_hash("test1234"),
            role="jobseeker",
            name="Kavya Nair"
        )
        db.session.add(js_user)
        db.session.flush()

        js_profile = JobSeekerProfile(
            user_id=js_user.id,
            first_name="Kavya",
            last_name="Nair",
            dob=date(1997, 6, 10),
            gender="Female",
            address="22 Brigade Road, Bangalore",
            pincode="560100",
            mobile="9876543215",
            father_husband_name="Mohan Nair",
            education_level="Graduate",
            preferred_location1="Bangalore",
            preferred_location2="Electronic City",
            employment_type="Full-time",
            skills="Administration, MS Office, English, Hindi, Kannada",
            city="Bangalore",
            state="Karnataka",
            verified=True,
            payment_status="success"
        )
        db.session.add(js_profile)

        # ========================================================
        # 2. 10 Employers + coordinates within ~100 km of 12.8375, 77.6501
        # ========================================================
        center_lat = 12.8375
        center_lng = 77.6501

        # 10 slightly different locations (approx 1-100 km away)
        employer_coords = [
            (12.8375, 77.6501),   # exactly the centre
            (12.8400, 77.6550),   # ~600 m
            (12.8300, 77.6400),   # ~1.5 km
            (12.8600, 77.6800),   # ~4.5 km
            (12.8100, 77.7200),   # ~8.5 km
            (12.7800, 77.6900),   # ~7 km
            (12.9000, 77.6000),   # ~8 km
            (12.7500, 77.5500),   # ~15 km
            (12.6500, 77.4000),   # ~33 km
            (12.5000, 77.2000)    # ~60 km (still within 100 km)
        ]

        employers = []
        for i, (lat, lng) in enumerate(employer_coords, start=1):
            email = f"company{i}@example.com"
            if not User.query.filter_by(email=email).first():
                u = User(
                    email=email,
                    password_hash=generate_password_hash("test1234"),
                    role="employer",
                    name=f"Test Company {i}"
                )
                db.session.add(u)
                db.session.flush()

                ep = EmployerProfile(
                    user_id=u.id,
                    business_name=f"Test Business {i}",
                    business_address=f"{i} Test Lane, Bangalore",
                    gst_number=f"29AAACT{i:04d}A1Z0",
                    business_type="Service",
                    contact_person_name=f"Manager {i}",
                    contact_person_phone=f"99999999{10+i:02d}",
                    city="Bangalore",
                    state="Karnataka",
                    pincode="560100",
                    verified=True,
                    payment_status="success",
                    dob=date(1980 + i, 1, 10),
                    latitude=lat,
                    longitude=lng
                )
                db.session.add(ep)
                employers.append(ep)
            else:
                existing = EmployerProfile.query.filter_by(user_id=User.query.filter_by(email=email).first().id).first()
                if existing:
                    employers.append(existing)

        db.session.commit()

        # ========================================================
        # 3. 10 Jobs – one per employer
        # ========================================================
        job_templates = [
            "Delivery Associate",
            "Customer Service Executive",
            "Warehouse Helper",
            "Security Guard",
            "Store Helper",
            "Cashier",
            "Floor Supervisor",
            "Data Entry Operator",
            "Warehouse Associate",
            "Delivery Boy"
        ]
        job_descriptions = [
            "Deliver packages in Bangalore. Own bike and license required.",
            "Handle customer calls and emails. Good communication skills needed.",
            "Assist in packing and moving inventory in the warehouse.",
            "Patrol the premises and ensure safety of employees.",
            "Stock shelves and assist customers on the floor.",
            "Handle billing counter and cash transactions.",
            "Supervise a team of helpers and ensure smooth operations.",
            "Enter product details into the system. Basic computer knowledge required.",
            "Pack and ship orders, manage inventory in the warehouse.",
            "Deliver products to customers around Bangalore. Bike required."
        ]
        job_types = [
            "Full-time", "Full-time", "Part-time", "Full-time",
            "Part-time", "Full-time", "Full-time", "Full-time",
            "Full-time", "Full-time"
        ]
        salaries = [
            "₹18,000 – ₹22,000/month",
            "₹20,000 – ₹25,000/month",
            "₹12,000 – ₹15,000/month",
            "₹15,000/month",
            "₹11,000 – ₹14,000/month",
            "₹14,000 – ₹18,000/month",
            "₹20,000 – ₹25,000/month",
            "₹15,000/month",
            "₹16,000 – ₹20,000/month",
            "₹18,000 – ₹22,000/month"
        ]

        for idx, employer in enumerate(employers):
            if not Job.query.filter_by(employer_id=employer.id, job_name=job_templates[idx]).first():
                job = Job(
                    employer_id=employer.id,
                    employer_name=employer.business_name,
                    employer_address=employer.business_address,
                    employer_mobile=employer.contact_person_phone,
                    employer_city=employer.city,
                    employer_state=employer.state,
                    employer_pincode=employer.pincode,
                    job_name=job_templates[idx],
                    job_description=job_descriptions[idx],
                    job_type=job_types[idx],
                    committed_salary=salaries[idx],
                    location="Bangalore",
                    vacancies=idx + 2,
                    status="Open",
                    deleted=False
                )
                db.session.add(job)

        db.session.commit()

        # ========================================================
        # 4. (Optional) one application for testing
        # ========================================================
        kavya = User.query.filter_by(email="kavya@example.com").first()
        first_job = Job.query.first()
        if kavya and first_job and not JobApplication.query.filter_by(job_id=first_job.id, applicant_id=kavya.id).first():
            db.session.add(JobApplication(job_id=first_job.id, applicant_id=kavya.id, status="Pending"))

        db.session.commit()

        print("Database seeded with 10 employers / 10 jobs within 100 km of the test location.")

if __name__ == '__main__':
    seed()
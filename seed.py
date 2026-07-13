import os
import sys
from datetime import date, datetime
from werkzeug.security import generate_password_hash
from config import Config
from models import db, User, JobSeekerProfile, EmployerProfile, Job, JobApplication
from flask import Flask

# Create a minimal Flask app just for seeding
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def seed():
    with app.app_context():
        # Drop and recreate all tables (optional – comment out if you want to keep existing data)
        # db.drop_all()
        # db.create_all()

        # ----- 1. Create Jobseekers (6 entries, at least 2 with pincode 560100) -----
        js_data = [
            {
                "email": "rajesh@example.com",
                "password": "test1234",
                "name": "Rajesh Kumar",
                "profile": {
                    "first_name": "Rajesh",
                    "last_name": "Kumar",
                    "dob": date(1995, 5, 12),
                    "gender": "Male",
                    "address": "123 MG Road, Mumbai",
                    "pincode": "400001",          # not 560100
                    "mobile": "9876543210",
                    "father_husband_name": "Suresh Kumar",
                    "education_level": "Graduate",
                    "preferred_location1": "Mumbai",
                    "preferred_location2": "Thane",
                    "employment_type": "Full-time",
                    "skills": "Sales, Customer Service, Hindi, English",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "verified": True,
                    "payment_status": "success"
                }
            },
            {
                "email": "priya@example.com",
                "password": "test1234",
                "name": "Priya Sharma",
                "profile": {
                    "first_name": "Priya",
                    "last_name": "Sharma",
                    "dob": date(1998, 8, 23),
                    "gender": "Female",
                    "address": "45 Park Street, Delhi",
                    "pincode": "560100",          # changed to 560100 (was 110001)
                    "mobile": "9876543211",
                    "father_husband_name": "Ramesh Sharma",
                    "education_level": "Post Graduate",
                    "preferred_location1": "Delhi",
                    "preferred_location2": "Noida",
                    "employment_type": "Part-time",
                    "skills": "Data Entry, Computer Basics, Hindi, English",
                    "city": "Delhi",
                    "state": "Delhi",
                    "verified": True,
                    "payment_status": "success"
                }
            },
            {
                "email": "amit@example.com",
                "password": "test1234",
                "name": "Amit Patel",
                "profile": {
                    "first_name": "Amit",
                    "last_name": "Patel",
                    "dob": date(1993, 3, 5),
                    "gender": "Male",
                    "address": "78 CG Road, Ahmedabad",
                    "pincode": "380001",
                    "mobile": "9876543212",
                    "father_husband_name": "Mohan Patel",
                    "education_level": "12th",
                    "preferred_location1": "Ahmedabad",
                    "preferred_location2": "Vadodara",
                    "employment_type": "Full-time",
                    "skills": "Driving License, Delivery, Bike Riding, Hindi, Gujarati",
                    "city": "Ahmedabad",
                    "state": "Gujarat",
                    "verified": False,
                    "payment_status": "failed"
                }
            },
            {
                "email": "neha@example.com",
                "password": "test1234",
                "name": "Neha Gupta",
                "profile": {
                    "first_name": "Neha",
                    "last_name": "Gupta",
                    "dob": date(2000, 11, 18),
                    "gender": "Female",
                    "address": "12/A Civil Lines, Lucknow",
                    "pincode": "226001",
                    "mobile": "9876543213",
                    "father_husband_name": "Rajendra Gupta",
                    "education_level": "Graduate",
                    "preferred_location1": "Lucknow",
                    "preferred_location2": "Kanpur",
                    "employment_type": "Both",
                    "skills": "Beautician, Salon, Customer Service, Hindi",
                    "city": "Lucknow",
                    "state": "Uttar Pradesh",
                    "verified": True,
                    "payment_status": "success"
                }
            },
            {
                "email": "vikram@example.com",
                "password": "test1234",
                "name": "Vikram Singh",
                "profile": {
                    "first_name": "Vikram",
                    "last_name": "Singh",
                    "dob": date(1990, 1, 30),
                    "gender": "Male",
                    "address": "56/2 Defence Colony, Bangalore",
                    "pincode": "560001",
                    "mobile": "9876543214",
                    "father_husband_name": "Jaswant Singh",
                    "education_level": "Post Graduate",
                    "preferred_location1": "Bangalore",
                    "preferred_location2": "Mysore",
                    "preferred_location3": "Hyderabad",
                    "employment_type": "Full-time",
                    "skills": "Computer Repair, Mobile Repair, AC Repair, Plumbing, Electrical, Hindi, Kannada, English",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "verified": False,
                    "payment_status": "failed"
                }
            },
            # NEW jobseeker (6th) with pincode 560100
            {
                "email": "kavya@example.com",
                "password": "test1234",
                "name": "Kavya Nair",
                "profile": {
                    "first_name": "Kavya",
                    "last_name": "Nair",
                    "dob": date(1997, 6, 10),
                    "gender": "Female",
                    "address": "22 Brigade Road, Bangalore",
                    "pincode": "560100",          # 560100
                    "mobile": "9876543215",
                    "father_husband_name": "Mohan Nair",
                    "education_level": "Graduate",
                    "preferred_location1": "Bangalore",
                    "preferred_location2": "Electronic City",
                    "employment_type": "Full-time",
                    "skills": "Administration, MS Office, English, Hindi, Kannada",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "verified": True,
                    "payment_status": "success"
                }
            }
        ]

        for js in js_data:
            if not User.query.filter_by(email=js["email"]).first():
                user = User(
                    email=js["email"],
                    password_hash=generate_password_hash(js["password"]),
                    role="jobseeker",
                    name=js["name"]
                )
                db.session.add(user)
                db.session.flush()

                p = js["profile"]
                profile = JobSeekerProfile(
                    user_id=user.id,
                    first_name=p["first_name"],
                    last_name=p["last_name"],
                    dob=p["dob"],
                    gender=p["gender"],
                    address=p["address"],
                    pincode=p["pincode"],
                    mobile=p["mobile"],
                    father_husband_name=p["father_husband_name"],
                    education_level=p["education_level"],
                    preferred_location1=p["preferred_location1"],
                    preferred_location2=p.get("preferred_location2"),
                    preferred_location3=p.get("preferred_location3"),
                    employment_type=p["employment_type"],
                    skills=p["skills"],
                    city=p["city"],
                    state=p["state"],
                    verified=p.get("verified", False),
                    payment_status=p.get("payment_status", "failed")
                )
                db.session.add(profile)

        # ----- 2. Create Employers (8 entries, at least 3 with pincode 560100) -----
        emp_data = [
            # Existing 3 (modified Amazon and Big Bazaar to pincode 560100)
            {
                "email": "amazon@example.com",
                "password": "test1234",
                "name": "Amazon India",
                "profile": {
                    "business_name": "Amazon India Pvt Ltd",
                    "business_address": "E-Commerce Park, Bangalore",
                    "gst_number": "29AAACB1419A1Z8",
                    "business_type": "Service",
                    "contact_person_name": "Suresh Reddy",
                    "contact_person_phone": "9999999991",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "pincode": "560100",          # changed to 560100 (was 560001)
                    "verified": True,
                    "payment_status": "success",
                    "dob": date(1985, 1, 1)
                }
            },
            {
                "email": "bigbazaar@example.com",
                "password": "test1234",
                "name": "Big Bazaar",
                "profile": {
                    "business_name": "Big Bazaar Retail Ltd",
                    "business_address": "55 Linking Road, Mumbai",
                    "gst_number": "27AAECB1234A1Z9",
                    "business_type": "Retail",
                    "contact_person_name": "Rohit Jain",
                    "contact_person_phone": "9999999992",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": "560100",          # changed to 560100 (was 400001)
                    "verified": True,
                    "payment_status": "success",
                    "dob": date(1980, 5, 15)
                }
            },
            {
                "email": "tata@example.com",
                "password": "test1234",
                "name": "Tata Motors",
                "profile": {
                    "business_name": "Tata Motors Ltd",
                    "business_address": "Industrial Area, Pune",
                    "gst_number": "27AAACT1234A1Z0",
                    "business_type": "Manufacturing",
                    "contact_person_name": "Anita Deshmukh",
                    "contact_person_phone": "9999999993",
                    "city": "Pune",
                    "state": "Maharashtra",
                    "pincode": "411001",          # not 560100
                    "verified": False,
                    "payment_status": "failed",
                    "dob": date(1978, 9, 20)
                }
            },
            # NEW employers (5 more) - 3 with pincode 560100, 2 with other pincodes
            {
                "email": "flipkart@example.com",
                "password": "test1234",
                "name": "Flipkart",
                "profile": {
                    "business_name": "Flipkart India Pvt Ltd",
                    "business_address": "Embassy Tech Village, Bangalore",
                    "gst_number": "29AAACF1234A1Z1",
                    "business_type": "E-commerce",
                    "contact_person_name": "Ravi Kumar",
                    "contact_person_phone": "9999999994",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "pincode": "560100",          # 560100
                    "verified": True,
                    "payment_status": "success",
                    "dob": date(1987, 7, 19)
                }
            },
            {
                "email": "swiggy@example.com",
                "password": "test1234",
                "name": "Swiggy",
                "profile": {
                    "business_name": "Swiggy Food Delivery",
                    "business_address": "HSR Layout, Bangalore",
                    "gst_number": "29AAACS1234A1Z2",
                    "business_type": "Food Delivery",
                    "contact_person_name": "Meera Iyer",
                    "contact_person_phone": "9999999995",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "pincode": "560100",          # 560100
                    "verified": True,
                    "payment_status": "success",
                    "dob": date(1990, 3, 12)
                }
            },
            {
                "email": "zomato@example.com",
                "password": "test1234",
                "name": "Zomato",
                "profile": {
                    "business_name": "Zomato Media Pvt Ltd",
                    "business_address": "Indiranagar, Bangalore",
                    "gst_number": "29AAACZ1234A1Z3",
                    "business_type": "Food Tech",
                    "contact_person_name": "Amit Singh",
                    "contact_person_phone": "9999999996",
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "pincode": "560100",          # 560100 (now we have at least 3 employers with 560100)
                    "verified": False,
                    "payment_status": "pending",
                    "dob": date(1988, 11, 5)
                }
            },
            {
                "email": "adani@example.com",
                "password": "test1234",
                "name": "Adani Group",
                "profile": {
                    "business_name": "Adani Enterprises Ltd",
                    "business_address": "Shantigram, Ahmedabad",
                    "gst_number": "24AAACA1234A1Z4",
                    "business_type": "Infrastructure",
                    "contact_person_name": "Gautam Shah",
                    "contact_person_phone": "9999999997",
                    "city": "Ahmedabad",
                    "state": "Gujarat",
                    "pincode": "380009",          # not 560100
                    "verified": True,
                    "payment_status": "success",
                    "dob": date(1975, 4, 25)
                }
            },
            {
                "email": "reliance@example.com",
                "password": "test1234",
                "name": "Reliance Retail",
                "profile": {
                    "business_name": "Reliance Retail Ltd",
                    "business_address": "Maker Chambers, Mumbai",
                    "gst_number": "27AAACR1234A1Z5",
                    "business_type": "Retail",
                    "contact_person_name": "Nisha Sharma",
                    "contact_person_phone": "9999999998",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": "400021",          # not 560100
                    "verified": False,
                    "payment_status": "failed",
                    "dob": date(1982, 8, 30)
                }
            }
        ]

        for emp in emp_data:
            if not User.query.filter_by(email=emp["email"]).first():
                user = User(
                    email=emp["email"],
                    password_hash=generate_password_hash(emp["password"]),
                    role="employer",
                    name=emp["name"]
                )
                db.session.add(user)
                db.session.flush()

                p = emp["profile"]
                profile = EmployerProfile(
                    user_id=user.id,
                    business_name=p["business_name"],
                    business_address=p["business_address"],
                    gst_number=p["gst_number"],
                    business_type=p["business_type"],
                    contact_person_name=p["contact_person_name"],
                    contact_person_phone=p["contact_person_phone"],
                    city=p["city"],
                    state=p["state"],
                    pincode=p["pincode"],
                    verified=p.get("verified", False),
                    payment_status=p.get("payment_status", "failed"),
                    dob=p["dob"]
                )
                db.session.add(profile)

        db.session.commit()  # flush all users and profiles

        # ----- 3. Create Jobs (same as before, but we can add more jobs from new employers if needed) -----
        # Get employer profiles (we'll pick some existing ones to keep job creation simple)
        emp_amazon = EmployerProfile.query.filter_by(business_name="Amazon India Pvt Ltd").first()
        emp_bigbazaar = EmployerProfile.query.filter_by(business_name="Big Bazaar Retail Ltd").first()
        emp_flipkart = EmployerProfile.query.filter_by(business_name="Flipkart India Pvt Ltd").first()  # new

        if emp_amazon and not Job.query.filter_by(employer_id=emp_amazon.id).first():
            jobs = [
                Job(
                    employer_id=emp_amazon.id,
                    employer_name=emp_amazon.business_name,
                    employer_address=emp_amazon.business_address,
                    employer_mobile=emp_amazon.contact_person_phone,
                    employer_city=emp_amazon.city,
                    employer_state=emp_amazon.state,
                    employer_pincode=emp_amazon.pincode,
                    job_name="Delivery Associate",
                    job_description="Deliver packages to customers in a timely manner. Must have a valid driving license and own bike.",
                    job_type="Full-time",
                    committed_salary="₹18,000 – ₹22,000/month",
                    location="Bangalore",
                    vacancies=5,
                    status="Open",
                    deleted=False
                ),
                Job(
                    employer_id=emp_amazon.id,
                    employer_name=emp_amazon.business_name,
                    employer_address=emp_amazon.business_address,
                    employer_mobile=emp_amazon.contact_person_phone,
                    employer_city=emp_amazon.city,
                    employer_state=emp_amazon.state,
                    employer_pincode=emp_amazon.pincode,
                    job_name="Customer Service Executive",
                    job_description="Handle customer queries via phone and email. Good communication skills required.",
                    job_type="Full-time",
                    committed_salary="₹20,000 – ₹25,000/month",
                    location="Bangalore",
                    vacancies=2,
                    status="Open",
                    deleted=False
                )
            ]
            for j in jobs:
                db.session.add(j)

        if emp_bigbazaar and not Job.query.filter_by(employer_id=emp_bigbazaar.id).first():
            jobs = [
                Job(
                    employer_id=emp_bigbazaar.id,
                    employer_name=emp_bigbazaar.business_name,
                    employer_address=emp_bigbazaar.business_address,
                    employer_mobile=emp_bigbazaar.contact_person_phone,
                    employer_city=emp_bigbazaar.city,
                    employer_state=emp_bigbazaar.state,
                    employer_pincode=emp_bigbazaar.pincode,
                    job_name="Store Helper",
                    job_description="Assist in stocking shelves, managing inventory, and helping customers.",
                    job_type="Part-time",
                    committed_salary="₹12,000 – ₹15,000/month",
                    location="Mumbai",
                    vacancies=3,
                    status="Open",
                    deleted=False
                ),
                Job(
                    employer_id=emp_bigbazaar.id,
                    employer_name=emp_bigbazaar.business_name,
                    employer_address=emp_bigbazaar.business_address,
                    employer_mobile=emp_bigbazaar.contact_person_phone,
                    employer_city=emp_bigbazaar.city,
                    employer_state=emp_bigbazaar.state,
                    employer_pincode=emp_bigbazaar.pincode,
                    job_name="Cashier",
                    job_description="Handle billing counter and cash transactions. Basic computer knowledge required.",
                    job_type="Full-time",
                    committed_salary="₹15,000 – ₹18,000/month",
                    location="Mumbai",
                    vacancies=1,
                    status="Open",
                    deleted=False
                )
            ]
            for j in jobs:
                db.session.add(j)

        # Optionally add jobs from Flipkart (new employer)
        if emp_flipkart and not Job.query.filter_by(employer_id=emp_flipkart.id).first():
            jobs = [
                Job(
                    employer_id=emp_flipkart.id,
                    employer_name=emp_flipkart.business_name,
                    employer_address=emp_flipkart.business_address,
                    employer_mobile=emp_flipkart.contact_person_phone,
                    employer_city=emp_flipkart.city,
                    employer_state=emp_flipkart.state,
                    employer_pincode=emp_flipkart.pincode,
                    job_name="Warehouse Associate",
                    job_description="Pack and ship orders, manage inventory in the warehouse.",
                    job_type="Full-time",
                    committed_salary="₹16,000 – ₹20,000/month",
                    location="Bangalore",
                    vacancies=4,
                    status="Open",
                    deleted=False
                )
            ]
            for j in jobs:
                db.session.add(j)

        db.session.commit()

        # ----- 4. Create Applications (same as before, but we can add more applications) -----
        job1 = Job.query.filter_by(job_name="Delivery Associate").first()
        job2 = Job.query.filter_by(job_name="Customer Service Executive").first()
        job3 = Job.query.filter_by(job_name="Store Helper").first()
        job4 = Job.query.filter_by(job_name="Cashier").first()
        job5 = Job.query.filter_by(job_name="Warehouse Associate").first()  # new job

        # Get some jobseeker users
        js1 = User.query.filter_by(email="rajesh@example.com").first()
        js2 = User.query.filter_by(email="priya@example.com").first()
        js3 = User.query.filter_by(email="amit@example.com").first()
        js4 = User.query.filter_by(email="neha@example.com").first()
        js5 = User.query.filter_by(email="vikram@example.com").first()
        js6 = User.query.filter_by(email="kavya@example.com").first()  # new

        # Check if applications already exist to avoid duplicates
        if js1 and job1 and not JobApplication.query.filter_by(job_id=job1.id, applicant_id=js1.id).first():
            db.session.add(JobApplication(job_id=job1.id, applicant_id=js1.id, status="Pending"))
        if js2 and job3 and not JobApplication.query.filter_by(job_id=job3.id, applicant_id=js2.id).first():
            db.session.add(JobApplication(job_id=job3.id, applicant_id=js2.id, status="Pending"))
        if js3 and job4 and not JobApplication.query.filter_by(job_id=job4.id, applicant_id=js3.id).first():
            db.session.add(JobApplication(job_id=job4.id, applicant_id=js3.id, status="Pending"))
        if js4 and job2 and not JobApplication.query.filter_by(job_id=job2.id, applicant_id=js4.id).first():
            db.session.add(JobApplication(job_id=job2.id, applicant_id=js4.id, status="Pending"))
        if js5 and job1 and not JobApplication.query.filter_by(job_id=job1.id, applicant_id=js5.id).first():
            db.session.add(JobApplication(job_id=job1.id, applicant_id=js5.id, status="Pending"))
        # New application for the new jobseeker
        if js6 and job5 and not JobApplication.query.filter_by(job_id=job5.id, applicant_id=js6.id).first():
            db.session.add(JobApplication(job_id=job5.id, applicant_id=js6.id, status="Pending"))

        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed()
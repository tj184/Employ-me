import os
import uuid
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import DataRequired
from config import Config
from models import db, User, JobSeekerProfile, EmployerProfile, Job,JobApplication
from forms import LoginForm, SignupForm, ProfileForm, EmployerForm, INDIAN_CITIES, SKILLS_CHOICES,JobForm
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from admin import admin_app 
import csv
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from flask import jsonify, session
import requests
import time



app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    db.create_all()
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_image(file):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))   # instead of User.query.get

def role_required(role):
    def decorator(func):
        from functools import wraps
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied.', 'danger')
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return wrapper
    return decorator




@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            if not next_page:
                next_page = url_for('jobseeker_dashboard') if user.role == 'jobseeker' else url_for('employer_profile')
            return redirect(next_page)
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET','POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()

    email_preverified = False

    # ---- GET request: pre‑fill email if already verified ----
    if request.method == 'GET' and session.get('email_verified'):
        form.email.data = session.get('email_verified')
        email_preverified = True

    if form.validate_on_submit():
        # ---- reCAPTCHA verification ----
        token = request.form.get('g-recaptcha-response')
        if not token:
            flash('reCAPTCHA token missing. Please refresh and try again.', 'danger')
            return render_template('signup.html', form=form,
                                   email_preverified=(session.get('email_verified') == form.email.data))
        valid, error = verify_recaptcha(token)
        if not valid:
            flash(error, 'danger')
            return render_template('signup.html', form=form,
                                   email_preverified=(session.get('email_verified') == form.email.data))

        # ---- email verification check ----
        if session.get('email_verified') != form.email.data:
            flash('Please verify your email before signing up.', 'danger')
            return render_template('signup.html', form=form,
                                   email_preverified=(session.get('email_verified') == form.email.data))

        # ---- signup logic (unchanged) ----
        hashed_pw = generate_password_hash(form.password.data)
        user = User(
            email=form.email.data,
            password_hash=hashed_pw,
            role=form.role.data,
            name=form.name.data
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        # Clear the verified flag after successful signup
        session.pop('email_verified', None)
        flash('Account created! Complete your profile.', 'success')
        if user.role == 'jobseeker':
            return redirect(url_for('jobseeker_dashboard'))
        else:
            return redirect(url_for('employer_profile'))

    # ---- POST with validation errors or GET without verified email ----
    if request.method == 'POST':
        # If the submitted email matches the verified one, keep the verified state
        if session.get('email_verified') == request.form.get('email'):
            email_preverified = True

    return render_template('signup.html', form=form, email_preverified=email_preverified)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/jobseeker', methods=['GET', 'POST'])
@login_required
@role_required('jobseeker')
def jobseeker_dashboard():
    profile = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
    form = ProfileForm(obj=profile)

    locked_fields = [
        'first_name', 'last_name', 'middle_name', 'dob', 'gender', 'address',
        'pincode', 'mobile', 'father_husband_name', 'city', 'state', 'aadhar_card'
    ] if profile else []

    if profile:
        for field_name in locked_fields:
            field = getattr(form, field_name, None)
            if field:
                field.validators = [v for v in field.validators if not isinstance(v, DataRequired)]

    if form.validate_on_submit():
        if not profile:
            if not form.profile_pic.data:
                flash('Profile picture is required.', 'danger')
                return render_template('jobseeker_dashboard.html',
                                       form=form, profile=profile,
                                       cities=INDIAN_CITIES, locked_fields=locked_fields)
            if not form.aadhar_card.data:
                flash('Aadhaar card image is required.', 'danger')
                return render_template('jobseeker_dashboard.html',
                                       form=form, profile=profile,
                                       cities=INDIAN_CITIES, locked_fields=locked_fields)

        selected = form.selected_skills.data
        skills_list = []
        if selected:
            label_map = dict(SKILLS_CHOICES)
            skills_list.extend([label_map.get(s, s) for s in selected])
        if form.custom_skills.data and form.custom_skills.data.strip():
            skills_list.extend([s.strip() for s in form.custom_skills.data.split(',') if s.strip()])
        if not skills_list:
            flash('Please select at least one skill or enter a custom skill.', 'danger')
            return render_template('jobseeker_dashboard.html',
                                   form=form, profile=profile,
                                   cities=INDIAN_CITIES, locked_fields=locked_fields)

        if not profile:
            profile = JobSeekerProfile(user_id=current_user.id)
            db.session.add(profile)

            profile.first_name = form.first_name.data
            profile.middle_name = form.middle_name.data
            profile.last_name = form.last_name.data
            profile.dob = form.dob.data
            profile.gender = form.gender.data
            profile.address = form.address.data
            profile.pincode = form.pincode.data
            profile.mobile = form.mobile.data
            profile.father_husband_name = form.father_husband_name.data
            profile.city = form.city.data
            profile.state = form.state.data

        profile.education_level = form.education_level.data
        profile.education_other = form.education_other.data if form.education_level.data == 'Others' else None
        profile.preferred_location1 = form.preferred_location1.data
        profile.preferred_location2 = form.preferred_location2.data or None
        profile.preferred_location3 = form.preferred_location3.data or None
        profile.employment_type = form.employment_type.data
        profile.skills = ', '.join(skills_list)

        if form.profile_pic.data:
            old = profile.profile_pic
            filename = save_image(form.profile_pic.data)
            if filename:
                if old and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], old)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old))
                profile.profile_pic = filename

        if not profile.id:
            if form.aadhar_card.data:
                filename = save_image(form.aadhar_card.data)
                if filename:
                    profile.aadhar_card = filename

        db.session.commit()
        flash('Profile saved successfully!', 'success')
        return redirect(url_for('jobseeker_dashboard'))

    if profile:
        form.first_name.data = profile.first_name
        form.middle_name.data = profile.middle_name
        form.last_name.data = profile.last_name
        form.dob.data = profile.dob
        form.gender.data = profile.gender
        form.address.data = profile.address
        form.pincode.data = profile.pincode
        form.mobile.data = profile.mobile
        form.father_husband_name.data = profile.father_husband_name
        form.city.data = profile.city
        form.state.data = profile.state
        form.education_level.data = profile.education_level
        form.education_other.data = profile.education_other
        form.preferred_location1.data = profile.preferred_location1
        form.preferred_location2.data = profile.preferred_location2
        form.preferred_location3.data = profile.preferred_location3
        form.employment_type.data = profile.employment_type

        if profile.skills:
            stored_skills = [s.strip() for s in profile.skills.split(',')]
            label_to_value = {v: k for k, v in SKILLS_CHOICES}
            selected_vals = []
            custom_remaining = []
            for skill in stored_skills:
                if skill in label_to_value:
                    selected_vals.append(label_to_value[skill])
                else:
                    custom_remaining.append(skill)
            form.selected_skills.data = selected_vals
            form.custom_skills.data = ', '.join(custom_remaining) if custom_remaining else ''
        else:
            form.selected_skills.data = []

    return render_template('jobseeker_dashboard.html',
                           form=form,
                           profile=profile,
                           cities=INDIAN_CITIES,
                           locked_fields=locked_fields)

@app.route('/employer/profile', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def employer_profile():
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    form = EmployerForm(obj=profile)

    locked_fields = [
        'business_name', 'business_address', 'gst_number', 'business_type',
        'city', 'state', 'pincode'
    ] if profile else []

    if profile:
        for field_name in locked_fields:
            field = getattr(form, field_name, None)
            if field:
                field.validators = [v for v in field.validators if not isinstance(v, DataRequired)]

    if form.validate_on_submit():
        # ---- Extra validation for NEW profiles ----
        if not profile and not form.profile_pic.data:
            flash('Business profile picture is required.', 'danger')
            return render_template('employer_profile.html',
                                   form=form,
                                   profile=profile,
                                   locked_fields=locked_fields)

        if not profile:
            profile = EmployerProfile(user_id=current_user.id)
            db.session.add(profile)

            profile.business_name = form.business_name.data
            profile.business_address = form.business_address.data
            profile.gst_number = form.gst_number.data
            profile.business_type = form.business_type.data
            profile.city = form.city.data
            profile.state = form.state.data
            profile.pincode = form.pincode.data

        # Always editable fields
        profile.contact_person_name = form.contact_person_name.data
        profile.contact_person_phone = form.contact_person_phone.data
        profile.dob = form.dob.data

        # Profile picture (always updatable)
        if form.profile_pic.data:
            old = profile.profile_pic
            filename = save_image(form.profile_pic.data)
            if filename:
                if old and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], old)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old))
                profile.profile_pic = filename

        db.session.commit()
        flash('Business profile saved!', 'success')
        return redirect(url_for('hire_dashboard'))

    # Pre-populate form for GET
    if profile:
        form.business_name.data = profile.business_name
        form.business_address.data = profile.business_address
        form.gst_number.data = profile.gst_number
        form.business_type.data = profile.business_type
        form.city.data = profile.city
        form.state.data = profile.state
        form.pincode.data = profile.pincode
        form.contact_person_name.data = profile.contact_person_name
        form.contact_person_phone.data = profile.contact_person_phone
        form.dob.data = profile.dob

    return render_template('employer_profile.html',
                           form=form,
                           profile=profile,
                           locked_fields=locked_fields)

def payment_required(f):
    """Redirects user if payment_status is not 'success'."""
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role == 'jobseeker':
            profile = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
        else:
            profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()

        if not profile or profile.payment_status != 'success':
            flash('Please complete the payment to access this feature.', 'warning')
            if current_user.role == 'jobseeker':
                return redirect(url_for('jobseeker_dashboard'))
            else:
                return redirect(url_for('employer_profile'))   # changed from 'index' to 'employer_profile'
        return f(*args, **kwargs)
    return decorated

@app.route('/hire')
@login_required
@role_required('employer')
@payment_required
def hire_dashboard():
    employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer_profile:
        flash('Please complete your business profile first.', 'warning')
        return redirect(url_for('employer_profile'))

    # Check if employer is verified
    if not employer_profile.verified:
        return redirect(url_for('verification_pending'))

    profiles = JobSeekerProfile.query.filter_by(verified=True).all()
    return render_template('hire_dashboard.html', profiles=profiles)


@app.route('/verification-pending')
@login_required
@role_required('employer')
def verification_pending():
    return render_template('verification_pending.html')

@app.route('/jobseeker/verification-pending')
@login_required
@role_required('jobseeker')
def jobseeker_verification_pending():
    return render_template('jobseeker_verification_pending.html')

@app.route('/view/<int:profile_id>')
@login_required
@role_required('employer')
@payment_required
def view_profile(profile_id):
    profile = JobSeekerProfile.query.get_or_404(profile_id)
    return render_template('view_profile.html', profile=profile)

# ---------- New: Delete account ----------
@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'GET':
        return render_template('delete_account.html')

    # POST – verify DOB and delete
    dob_str = request.form.get('dob')
    if not dob_str:
        flash('Please enter your date of birth.', 'danger')
        return redirect(url_for('delete_account'))

    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
        return redirect(url_for('delete_account'))

    # Check against the correct profile
    if current_user.role == 'jobseeker':
        profile = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
    else:
        profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()

    if not profile or profile.dob != dob:
        flash('Date of birth does not match our records. Account not deleted.', 'danger')
        return redirect(url_for('delete_account'))

    # All good – delete the user (cascade removes the profile)
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    flash('Your account has been permanently deleted. You can now create a new account with a different role.', 'success')
    return redirect(url_for('signup'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content='Page not found'), 404

def load_testimonials():
    testimonials = []
    try:
        with open('testimonials.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get('email', '').strip()
                image_file = None
                if email:
                    user = User.query.filter_by(email=email).first()
                    if user:
                        if user.role == 'jobseeker':
                            profile = JobSeekerProfile.query.filter_by(user_id=user.id).first()
                            if profile and profile.profile_pic:
                                image_file = profile.profile_pic
                        # For employers, we intentionally do NOT try to get a picture;
                        # image_file remains None, which triggers the default icon.
                testimonials.append({
                    'city': row.get('city', ''),
                    'name': row.get('name', ''),
                    'review': row.get('review', ''),
                    'type': row.get('type', ''),
                    'image_file': image_file
                })
    except FileNotFoundError:
        pass
    return testimonials

@app.route('/')
def index():
    testimonials = load_testimonials()
    return render_template('index.html', testimonials=testimonials)

def send_otp_email(to_email, otp):
    api_key = os.environ.get('RESEND_API_KEY')
    from_email = os.environ.get('EMAIL_USER')
    if not api_key or not from_email:
        raise Exception("Resend credentials not configured")

    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": f"Employ-me <{from_email}>",   # You can change "Employ-me" to any name
            "to": [to_email],
            "subject": "Employ-me Email Verification OTP",
            "text": f"Your OTP is {otp}. It is valid for 5 minutes."
        }
    )
    if response.status_code != 200:
        raise Exception(f"Resend error: {response.text}")

@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    token = data.get('g-recaptcha-response')

    if not email:
        return jsonify({'success': False, 'message': 'Email required'}), 400

    # reCAPTCHA verification
    if not token:
        return jsonify({'success': False, 'message': 'reCAPTCHA token missing'}), 400
    valid, error = verify_recaptcha(token)
    if not valid:
        return jsonify({'success': False, 'message': error}), 400

    # 🔒 Check if email already registered
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'This email is already registered.'}), 400

    # OTP logic (unchanged)
    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['otp_email'] = email
    session['otp_expiry'] = time.time() + 300

    try:
        send_otp_email(email, otp)
        return jsonify({'success': True, 'message': 'OTP sent'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    otp = data.get('otp')
    email = data.get('email')

    if (session.get('otp') == otp and
        session.get('otp_email') == email and
        time.time() < session.get('otp_expiry')):
        # OTP is valid
        session.pop('otp', None)
        session.pop('otp_expiry', None)
        session['email_verified'] = email
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Invalid OTP or expired'}), 400

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')

    # POST – check email and send OTP
    email = request.form.get('email', '').strip()
    if not email:
        flash('Please enter your email address.', 'danger')
        return render_template('forgot_password.html')

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('No account found with that email.', 'danger')
        return render_template('forgot_password.html')

    # Generate OTP and store in session
    otp = str(random.randint(100000, 999999))
    session['reset_otp'] = otp
    session['reset_otp_email'] = email
    session['reset_otp_expiry'] = time.time() + 300  # 5 minutes

    try:
        send_otp_email(email, otp)
        flash('OTP sent to your email. Valid for 5 minutes.', 'success')
        return redirect(url_for('verify_reset_otp'))
    except Exception as e:
        flash('Failed to send OTP. Please try again later.', 'danger')
        return render_template('forgot_password.html')


@app.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    if request.method == 'GET':
        return render_template('verify_reset_otp.html')

    # POST – verify OTP
    otp = request.form.get('otp', '').strip()
    if (session.get('reset_otp') == otp and
        time.time() < session.get('reset_otp_expiry', 0)):
        # OTP valid – allow password reset
        session.pop('reset_otp', None)
        session.pop('reset_otp_expiry', None)
        session['reset_allowed_email'] = session.get('reset_otp_email')
        return redirect(url_for('reset_password'))
    else:
        flash('Invalid OTP or expired.', 'danger')
        return render_template('verify_reset_otp.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        if not session.get('reset_allowed_email'):
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('forgot_password'))
        return render_template('reset_password.html')

    # POST – set new password
    if not session.get('reset_allowed_email'):
        flash('Session expired. Please start again.', 'danger')
        return redirect(url_for('forgot_password'))

    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    if not password or len(password) < 8:
        flash('Password must be at least 8 characters.', 'danger')
        return render_template('reset_password.html')
    if password != confirm:
        flash('Passwords do not match.', 'danger')
        return render_template('reset_password.html')

    email = session.pop('reset_allowed_email')
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('forgot_password'))

    user.password_hash = generate_password_hash(password)
    db.session.commit()
    flash('Password reset successfully. You can now log in.', 'success')
    return redirect(url_for('login'))

def verify_recaptcha(token):
    secret = os.environ.get('RECAPTCHA_SECRET_KEY')
    if not secret:
        return False, 'reCAPTCHA secret key not configured'

    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={'secret': secret, 'response': token}
    )
    result = response.json()
    if result.get('success') and result.get('score', 0) >= 0.5:  # threshold, adjust if needed
        return True, None
    return False, 'reCAPTCHA verification failed. Are you a robot?'

@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # ---- Collect form data ----
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # ---- Validation ----
        if not all([name, email, subject, message]):
            flash('All fields are required.', 'danger')
            return render_template('contact.html')

        # ---- Rate limit: max 2 messages per 24 hours ----
        now = time.time()
        window = 24 * 60 * 60  # 24 hours in seconds
        # Use session key to track count and first request time
        if 'contact_count' not in session or 'contact_first_time' not in session:
            session['contact_count'] = 0
            session['contact_first_time'] = now

        # Reset the window if 24 hours have passed
        if now - session['contact_first_time'] > window:
            session['contact_count'] = 0
            session['contact_first_time'] = now

        if session['contact_count'] >= 2:
            flash('You have reached the maximum of 2 messages per 24 hours. Please try again later.', 'danger')
            return render_template('contact.html')

        # ---- Send email via Resend ----
        try:
            api_key = os.environ.get('RESEND_API_KEY')
            from_email = os.environ.get('EMAIL_USER')
            if not api_key or not from_email:
                flash('Email service not configured. Please try again later.', 'danger')
                return render_template('contact.html')

            email_body = f"""
            New message from {name} ({email})

            Subject: {subject}

            Message:
            {message}
            """
            response = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": f"Employ-me Contact <{from_email}>",
                    "to": ["tanishjain184@gmail.com"],
                    "reply_to": email,
                    "subject": f"Contact: {subject}",
                    "text": email_body
                }
            )
            if response.status_code != 200:
                raise Exception(f"Resend error: {response.text}")

            # Increment count only after successful send
            session['contact_count'] += 1
            flash('Your message has been sent successfully! We will get back to you soon.', 'success')
        except Exception as e:
            flash('Failed to send message. Please try again later.', 'danger')
            print(f"Contact email error: {e}")  # optional logging

        return render_template('contact.html')

    # GET request
    return render_template('contact.html')

@app.route('/job/create', methods=['GET', 'POST'])
@login_required
@role_required('employer')
@payment_required
def create_job():
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer:
        flash('Please complete your business profile first.', 'warning')
        return redirect(url_for('employer_profile'))

    # ---- Verification gate ----
    if not employer.verified:
        return redirect(url_for('verification_pending'))

    # ---- Rate limiter: max 3 jobs per 24 hours ----
    since = datetime.utcnow() - timedelta(hours=24)
    job_count = Job.query.filter(Job.employer_id == employer.id,
                                 Job.created_at >= since).count()
    if job_count >= 3:
        flash('You have reached the maximum of 3 job postings in 24 hours. Please try again later.', 'danger')
        return redirect(url_for('my_jobs'))

    form = JobForm()
    if form.validate_on_submit():
        job = Job(
            employer_id=employer.id,
            employer_name=employer.business_name,
            employer_address=employer.business_address,
            employer_mobile=employer.contact_person_phone,
            employer_city=employer.city,
            employer_state=employer.state,
            employer_pincode=employer.pincode,
            job_name=form.job_name.data,
            job_description=form.job_description.data,
            job_type=form.job_type.data,
            committed_salary=form.committed_salary.data,
            location=form.location.data,
            vacancies=int(form.vacancies.data) if form.vacancies.data.isdigit() else 1,
            status='Open'
        )
        db.session.add(job)
        db.session.commit()
        flash('Job created successfully!', 'success')
        return redirect(url_for('my_jobs'))

    return render_template('create_job.html', form=form)


@app.route('/job/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
@role_required('employer')
@payment_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()

    # Ensure the job belongs to the current employer
    if not employer or job.employer_id != employer.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('my_jobs'))

    # ---- Verification gate ----
    if not employer.verified:
        return redirect(url_for('verification_pending'))

    form = JobForm(obj=job)
    if form.validate_on_submit():
        job.job_name = form.job_name.data
        job.job_description = form.job_description.data
        job.job_type = form.job_type.data
        job.committed_salary = form.committed_salary.data
        job.location = form.location.data
        job.vacancies = int(form.vacancies.data) if form.vacancies.data.isdigit() else job.vacancies
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('my_jobs'))

    # Pre‑populate vacancies as string for the form
    if request.method == 'GET':
        form.vacancies.data = str(job.vacancies)

    return render_template('create_job.html', form=form, edit_mode=True, job=job)


@app.route('/job/delete/<int:job_id>')
@login_required
@role_required('employer')
@payment_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()

    if not employer or job.employer_id != employer.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('my_jobs'))

    if not employer.verified:
        return redirect(url_for('verification_pending'))

    # Soft‑delete
    job.deleted = True
    db.session.commit()
    flash('Job deleted.', 'success')
    return redirect(url_for('my_jobs'))


@app.route('/my-jobs')
@login_required
@role_required('employer')
@payment_required
def my_jobs():
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer:
        flash('Please complete your business profile first.', 'warning')
        return redirect(url_for('employer_profile'))
    if not employer.verified:
        return redirect(url_for('verification_pending'))

    jobs = Job.query.filter_by(employer_id=employer.id, deleted=False).order_by(Job.created_at.desc()).all()
    return render_template('my_jobs.html', jobs=jobs)

@app.route('/jobs')
@login_required
@role_required('jobseeker')
@payment_required
def job_list():
    profile = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or not profile.verified:
        return redirect(url_for('jobseeker_verification_pending'))

    applied_job_ids = [
        app.job_id for app in JobApplication.query.filter_by(applicant_id=current_user.id).all()
    ]

    jobs_query = Job.query.filter(
        Job.status == 'Open',
        Job.deleted == False,
        ~Job.id.in_(applied_job_ids) if applied_job_ids else True
    )

    # ----- read filter params -----
    use_pincode = request.args.get('use_pincode', '0') == '1'
    job_types_str = request.args.get('job_types', '')
    city = request.args.get('city', '').strip()
    state = request.args.get('state', '').strip()
    min_vacancies = request.args.get('min_vacancies', '').strip()
    search = request.args.get('search', '').strip()

    # ----- apply filters -----
    from filters import (filter_by_pincode, filter_by_job_types,
                         filter_by_city, filter_by_state,
                         filter_by_min_vacancies, filter_by_search)

    if use_pincode:
        jobs_query = filter_by_pincode(jobs_query, profile)
    if job_types_str:
        jobs_query = filter_by_job_types(jobs_query, job_types_str)
    if city:
        jobs_query = filter_by_city(jobs_query, city)
    if state:
        jobs_query = filter_by_state(jobs_query, state)
    if min_vacancies:
        jobs_query = filter_by_min_vacancies(jobs_query, min_vacancies)
    if search:
        jobs_query = filter_by_search(jobs_query, search)

    jobs = jobs_query.order_by(Job.created_at.desc()).all()

    # Pass the Indian cities list to the template for the dropdown
    from forms import INDIAN_CITIES
    return render_template('jobs_list.html',
                           jobs=jobs,
                           use_pincode=use_pincode,
                           job_types=job_types_str,
                           selected_city=city,
                           selected_state=state,
                           min_vacancies=min_vacancies,
                           search=search,
                           cities=INDIAN_CITIES)

@app.route('/job/apply/<int:job_id>')
@login_required
@role_required('jobseeker')
@payment_required
def apply_job(job_id):
    profile = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or not profile.verified:
        return redirect(url_for('jobseeker_verification_pending'))

    job = Job.query.get_or_404(job_id)
    # Check if already applied
    already = JobApplication.query.filter_by(job_id=job.id, applicant_id=current_user.id).first()
    if already:
        flash('You have already applied to this job.', 'info')
        return redirect(url_for('job_list'))

    application = JobApplication(job_id=job.id, applicant_id=current_user.id)
    db.session.add(application)
    db.session.commit()
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('my_applications'))

@app.route('/my-applications')
@login_required
@role_required('jobseeker')
@payment_required
def my_applications():
    profile = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or not profile.verified:
        return redirect(url_for('jobseeker_verification_pending'))
    applications = JobApplication.query.filter_by(applicant_id=current_user.id).order_by(JobApplication.applied_at.desc()).all()
    return render_template('my_applications.html', applications=applications)

@app.route('/employer/applicants/<int:job_id>')
@login_required
@role_required('employer')
@payment_required
def view_applicants(job_id):
    job = Job.query.get_or_404(job_id)
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer or job.employer_id != employer.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('my_jobs'))

    applications = JobApplication.query.filter_by(job_id=job.id).all()
    return render_template('applicants.html', job=job, applications=applications)

@app.route('/payment/simulate')
@login_required
def simulate_payment():
    if current_user.role == 'jobseeker':
        profile = JobSeekerProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your profile first.', 'danger')
            return redirect(url_for('jobseeker_dashboard'))
        profile.payment_status = 'success'
        db.session.commit()
        flash('Payment successful! You can now access all features.', 'success')
        return redirect(url_for('jobseeker_dashboard'))

    elif current_user.role == 'employer':
        profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your business profile first.', 'danger')
            return redirect(url_for('employer_profile'))
        profile.payment_status = 'success'
        db.session.commit()
        flash('Payment successful! You can now access all features.', 'success')
        return redirect(url_for('employer_profile'))

    flash('Access denied.', 'danger')
    return redirect(url_for('index'))

# Mount the admin app under /admin
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/admin': admin_app
})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
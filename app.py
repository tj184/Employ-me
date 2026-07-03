import os
import uuid
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import DataRequired
from config import Config
from models import db, User, JobSeekerProfile, EmployerProfile
from forms import LoginForm, SignupForm, ProfileForm, EmployerForm, INDIAN_CITIES, SKILLS_CHOICES
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from admin import admin_app  # make sure admin.py is importable
import csv

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
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
    return User.query.get(int(user_id))

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

# ---------- Routes ----------


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
    if form.validate_on_submit():
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
        flash('Account created! Complete your profile.', 'success')
        if user.role == 'jobseeker':
            return redirect(url_for('jobseeker_dashboard'))
        else:
            return redirect(url_for('employer_profile'))
    return render_template('signup.html', form=form)

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

    # Locked fields after first save (everything except contact details and DOB)
    locked_fields = [
        'business_name', 'business_address', 'gst_number', 'business_type',
        'city', 'state', 'pincode'
    ] if profile else []

    # Remove DataRequired validators from locked fields
    if profile:
        for field_name in locked_fields:
            field = getattr(form, field_name, None)
            if field:
                field.validators = [v for v in field.validators if not isinstance(v, DataRequired)]

    if form.validate_on_submit():
        if not profile:
            profile = EmployerProfile(user_id=current_user.id)
            db.session.add(profile)

            # New profile → assign all business fields (locked fields)
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
@app.route('/hire')
@login_required
@role_required('employer')
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

@app.route('/view/<int:profile_id>')
@login_required
@role_required('employer')
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
                testimonials.append(row)
    except FileNotFoundError:
        pass
    return testimonials

@app.route('/')
def index():
    testimonials = load_testimonials()
    return render_template('index.html', testimonials=testimonials)




# Mount the admin app under /admin
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/admin': admin_app
})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, JobSeekerProfile
from forms import LoginForm, SignupForm, ProfileForm, INDIAN_CITIES, SKILLS_CHOICES   # added INDIAN_CITIES

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

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

# Custom decorator for role-based access
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
@app.route('/')
def index():
    return render_template('index.html')

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
                next_page = url_for('jobseeker_dashboard') if user.role == 'jobseeker' else url_for('hire_dashboard')
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
        return redirect(url_for('jobseeker_dashboard') if user.role == 'jobseeker' else url_for('hire_dashboard'))
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

    if form.validate_on_submit():
        if not profile:
            profile = JobSeekerProfile(user_id=current_user.id)
            db.session.add(profile)

        # Name parts
        profile.first_name = form.first_name.data
        profile.middle_name = form.middle_name.data
        profile.last_name = form.last_name.data

        # Personal
        profile.dob = form.dob.data
        profile.gender = form.gender.data
        profile.address = form.address.data
        profile.pincode = form.pincode.data
        profile.mobile = form.mobile.data
        profile.father_husband_name = form.father_husband_name.data

        # NEW: City and State
        profile.city = form.city.data
        profile.state = form.state.data

        # Education
        profile.education_level = form.education_level.data
        profile.education_other = form.education_other.data if form.education_level.data == 'Others' else None

        # Work preferences (now text fields with autocomplete)
        profile.preferred_location1 = form.preferred_location1.data
        profile.preferred_location2 = form.preferred_location2.data or None
        profile.preferred_location3 = form.preferred_location3.data or None
        profile.employment_type = form.employment_type.data

        # Skills: combine selected checkboxes + custom text
        selected = form.selected_skills.data  # list of values
        skills_list = []
        if selected:
            label_map = dict(SKILLS_CHOICES)
            skills_list.extend([label_map.get(s, s) for s in selected])
        if form.custom_skills.data.strip():
            skills_list.extend([s.strip() for s in form.custom_skills.data.split(',') if s.strip()])
        profile.skills = ', '.join(skills_list) if skills_list else None

        # Images
        if form.profile_pic.data:
            old = profile.profile_pic
            filename = save_image(form.profile_pic.data)
            if filename:
                if old:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                profile.profile_pic = filename
        if form.aadhar_card.data:
            old = profile.aadhar_card
            filename = save_image(form.aadhar_card.data)
            if filename:
                if old:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                profile.aadhar_card = filename

        db.session.commit()
        flash('Profile saved successfully!', 'success')
        return redirect(url_for('jobseeker_dashboard'))

    # Pre-populate form for GET (if profile exists)
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
        # NEW: city and state
        form.city.data = profile.city
        form.state.data = profile.state
        form.education_level.data = profile.education_level
        form.education_other.data = profile.education_other
        form.preferred_location1.data = profile.preferred_location1
        form.preferred_location2.data = profile.preferred_location2
        form.preferred_location3.data = profile.preferred_location3
        form.employment_type.data = profile.employment_type
        # Pre-select skills checkboxes: we have stored labels; map back to values
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

    # Pass the full list of cities to the template for datalist
    return render_template('jobseeker_dashboard.html', form=form, profile=profile, cities=INDIAN_CITIES)

@app.route('/hire')
@login_required
@role_required('employer')
def hire_dashboard():
    profiles = JobSeekerProfile.query.all()
    return render_template('hire_dashboard.html', profiles=profiles)

@app.route('/view/<int:profile_id>')
@login_required
@role_required('employer')
def view_profile(profile_id):
    profile = JobSeekerProfile.query.get_or_404(profile_id)
    return render_template('view_profile.html', profile=profile)

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content='Page not found'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0')
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, JobSeekerProfile

admin_app = Flask(__name__, template_folder='admin_templates')
admin_app.config.from_object(Config)
admin_app.secret_key = 'admin-secret-key-change-me'

db.init_app(admin_app)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

def login_required_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@admin_app.route('/')
def root():
    return redirect(url_for('admin_login'))

@admin_app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('admin_login.html')

@admin_app.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))

@admin_app.route('/dashboard')
@login_required_admin
def admin_dashboard():
    pending_profiles = JobSeekerProfile.query.filter_by(verified=False).all()
    approved_profiles = JobSeekerProfile.query.filter_by(verified=True).all()
    return render_template('admin_dashboard.html',
                           pending=pending_profiles,
                           approved=approved_profiles)

@admin_app.route('/view/<int:profile_id>')
@login_required_admin
def admin_view_profile(profile_id):
    profile = JobSeekerProfile.query.get_or_404(profile_id)
    return render_template('admin_view_profile.html', profile=profile)

@admin_app.route('/approve/<int:profile_id>')
@login_required_admin
def admin_approve(profile_id):
    profile = JobSeekerProfile.query.get_or_404(profile_id)
    profile.verified = True
    db.session.commit()
    flash(f'Profile of {profile.first_name} {profile.last_name} has been approved.', 'success')
    return redirect(url_for('admin_dashboard'))
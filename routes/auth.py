"""
Authentication routes: register, login, logout, profile edit.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from extensions import db, bcrypt
from models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip().lower()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')
        role      = request.form.get('role', 'seeker')
        full_name = request.form.get('full_name', '').strip()

        # ── Validation ───────────────────────────────────────────────────────
        errors = []
        if not all([username, email, password, confirm, full_name]):
            errors.append('All fields are required.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        if role not in ('seeker', 'employer'):
            errors.append('Invalid role selected.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html', form=request.form)

        # ── Create user ──────────────────────────────────────────────────────
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username,
            email=email,
            password=hashed_pw,
            role=role,
            full_name=full_name,
        )
        # Extra employer fields
        if role == 'employer':
            user.company_name = request.form.get('company_name', '').strip()

        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact admin.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Redirect to originally-requested page or role dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(_dashboard_url(user))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name        = request.form.get('full_name', '').strip()
        current_user.phone            = request.form.get('phone', '').strip()
        current_user.location         = request.form.get('location', '').strip()
        current_user.bio              = request.form.get('bio', '').strip()
        current_user.skills           = request.form.get('skills', '').strip()
        current_user.experience_years = int(request.form.get('experience_years', 0) or 0)

        if current_user.is_employer:
            current_user.company_name        = request.form.get('company_name', '').strip()
            current_user.company_description = request.form.get('company_description', '').strip()
            current_user.website             = request.form.get('website', '').strip()

        # Password change (optional)
        new_pw  = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if new_pw:
            if new_pw != confirm:
                flash('Passwords do not match.', 'danger')
                return render_template('auth/profile.html')
            current_user.password = bcrypt.generate_password_hash(new_pw).decode('utf-8')

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')


# ── Helpers ───────────────────────────────────────────────────────────────────
def _dashboard_url(user):
    if user.is_admin:
        return url_for('admin.dashboard')
    if user.is_employer:
        return url_for('employer.dashboard')
    return url_for('dashboard.seeker_dashboard')

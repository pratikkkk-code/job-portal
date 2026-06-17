"""
Admin routes: dashboard, manage users, manage jobs, categories.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models import User, Job, Application, Category

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access only.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_users':    User.query.count(),
        'total_seekers':  User.query.filter_by(role='seeker').count(),
        'total_employers':User.query.filter_by(role='employer').count(),
        'total_jobs':     Job.query.count(),
        'active_jobs':    Job.query.filter_by(is_active=True).count(),
        'total_apps':     Application.query.count(),
    }
    recent_jobs  = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_jobs=recent_jobs, recent_users=recent_users)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    role   = request.args.get('role', '')
    search = request.args.get('q', '').strip()
    page   = request.args.get('page', 1, type=int)

    q = User.query
    if role:
        q = q.filter_by(role=role)
    if search:
        q = q.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )
    pagination = q.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', pagination=pagination, role=role, search=search)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate your own account.', 'warning')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'User {"activated" if user.is_active else "deactivated"}.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot delete your own account.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/jobs')
@login_required
@admin_required
def jobs():
    search   = request.args.get('q', '').strip()
    page     = request.args.get('page', 1, type=int)
    active   = request.args.get('active', '')

    q = Job.query
    if search:
        q = q.filter(Job.title.ilike(f'%{search}%'))
    if active == '1':
        q = q.filter_by(is_active=True)
    elif active == '0':
        q = q.filter_by(is_active=False)

    pagination = q.order_by(Job.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/jobs.html', pagination=pagination, search=search, active=active)


@admin_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted.', 'info')
    return redirect(url_for('admin.jobs'))


@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        icon = request.form.get('icon', 'bi-briefcase').strip()
        if name:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, icon=icon))
                db.session.commit()
                flash(f'Category "{name}" added.', 'success')
            else:
                flash('Category already exists.', 'warning')
    cats = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{cat.name}" deleted.', 'info')
    return redirect(url_for('admin.categories'))

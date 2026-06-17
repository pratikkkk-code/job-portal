"""
Employer routes: dashboard, post job, manage listings, view applicants.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from extensions import db
from models import Job, Application, Category, User

employer_bp = Blueprint('employer', __name__)


def employer_required(f):
    """Decorator: restrict to employer role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_employer:
            flash('Access restricted to employers.', 'warning')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@employer_bp.route('/dashboard')
@login_required
@employer_required
def dashboard():
    jobs = (
        Job.query
        .filter_by(employer_id=current_user.id)
        .order_by(Job.created_at.desc())
        .all()
    )
    total_apps = sum(j.application_count for j in jobs)
    active_jobs = sum(1 for j in jobs if j.is_active)

    return render_template(
        'employer/dashboard.html',
        jobs=jobs,
        total_apps=total_apps,
        active_jobs=active_jobs,
    )


@employer_bp.route('/post-job', methods=['GET', 'POST'])
@login_required
@employer_required
def post_job():
    categories = Category.query.all()

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        location    = request.form.get('location', '').strip()

        if not all([title, description, location]):
            flash('Title, description, and location are required.', 'danger')
            return render_template('employer/post_job.html', categories=categories, form=request.form)

        # Parse salary (optional)
        try:
            sal_min = int(request.form.get('salary_min') or 0) or None
            sal_max = int(request.form.get('salary_max') or 0) or None
        except ValueError:
            sal_min = sal_max = None

        # Parse deadline (optional)
        deadline_str = request.form.get('deadline', '').strip()
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                pass

        job = Job(
            title            = title,
            description      = description,
            location         = location,
            salary_min       = sal_min,
            salary_max       = sal_max,
            job_type         = request.form.get('job_type', 'Full-Time'),
            experience_level = request.form.get('experience_level', 'Mid-Level'),
            is_remote        = request.form.get('is_remote') == 'on',
            skills_required  = request.form.get('skills_required', '').strip(),
            category_id      = request.form.get('category_id', type=int),
            deadline         = deadline,
            employer_id      = current_user.id,
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully! ✅', 'success')
        return redirect(url_for('employer.dashboard'))

    return render_template('employer/post_job.html', categories=categories, form={})


@employer_bp.route('/job/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
@employer_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.employer_id != current_user.id:
        flash('You do not have permission to edit this job.', 'danger')
        return redirect(url_for('employer.dashboard'))

    categories = Category.query.all()

    if request.method == 'POST':
        job.title            = request.form.get('title', '').strip()
        job.description      = request.form.get('description', '').strip()
        job.location         = request.form.get('location', '').strip()
        job.job_type         = request.form.get('job_type', 'Full-Time')
        job.experience_level = request.form.get('experience_level', 'Mid-Level')
        job.is_remote        = request.form.get('is_remote') == 'on'
        job.skills_required  = request.form.get('skills_required', '').strip()
        job.category_id      = request.form.get('category_id', type=int)

        try:
            job.salary_min = int(request.form.get('salary_min') or 0) or None
            job.salary_max = int(request.form.get('salary_max') or 0) or None
        except ValueError:
            pass

        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            try:
                job.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                pass

        db.session.commit()
        flash('Job updated successfully.', 'success')
        return redirect(url_for('employer.dashboard'))

    return render_template('employer/edit_job.html', job=job, categories=categories)


@employer_bp.route('/job/<int:job_id>/toggle', methods=['POST'])
@login_required
@employer_required
def toggle_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('employer.dashboard'))

    job.is_active = not job.is_active
    db.session.commit()
    state = 'activated' if job.is_active else 'paused'
    flash(f'Job listing {state}.', 'info')
    return redirect(url_for('employer.dashboard'))


@employer_bp.route('/job/<int:job_id>/delete', methods=['POST'])
@login_required
@employer_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('employer.dashboard'))

    db.session.delete(job)
    db.session.commit()
    flash('Job listing deleted.', 'info')
    return redirect(url_for('employer.dashboard'))


@employer_bp.route('/job/<int:job_id>/applicants')
@login_required
@employer_required
def view_applicants(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('employer.dashboard'))

    apps = (
        Application.query
        .filter_by(job_id=job_id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template('employer/applicants.html', job=job, applications=apps)


@employer_bp.route('/application/<int:app_id>/status', methods=['POST'])
@login_required
@employer_required
def update_application_status(app_id):
    app = Application.query.get_or_404(app_id)

    # Verify the employer owns this job
    if app.job.employer_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('employer.dashboard'))

    new_status = request.form.get('status', 'Pending')
    valid = ('Pending', 'Reviewed', 'Shortlisted', 'Rejected', 'Hired')
    if new_status in valid:
        app.status = new_status
        db.session.commit()
        flash(f'Application marked as {new_status}.', 'success')

    return redirect(url_for('employer.view_applicants', job_id=app.job_id))

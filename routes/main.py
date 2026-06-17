"""
Main / public routes: homepage, job search, job detail.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from sqlalchemy import or_
from extensions import db
from models import Job, Category, Application, SavedJob, User

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page with featured jobs and category tiles."""
    featured_jobs = (
        Job.query
        .filter_by(is_active=True)
        .order_by(Job.created_at.desc())
        .limit(6)
        .all()
    )
    categories = Category.query.all()
    total_jobs  = Job.query.filter_by(is_active=True).count()
    total_emp   = User.query.filter_by(role='employer', is_active=True).count()
    total_seek  = User.query.filter_by(role='seeker',   is_active=True).count()

    return render_template(
        'index.html',
        featured_jobs=featured_jobs,
        categories=categories,
        total_jobs=total_jobs,
        total_emp=total_emp,
        total_seek=total_seek,
    )


@main_bp.route('/search')
def search():
    """Full-text job search with sidebar filters."""
    query_str    = request.args.get('q', '').strip()
    location     = request.args.get('location', '').strip()
    category_id  = request.args.get('category', type=int)
    job_type     = request.args.get('job_type', '').strip()
    exp_level    = request.args.get('exp_level', '').strip()
    remote_only  = request.args.get('remote') == '1'
    sort_by      = request.args.get('sort', 'newest')
    page         = request.args.get('page', 1, type=int)

    jobs_q = Job.query.filter_by(is_active=True)

    # Keyword search across title + description + skills
    if query_str:
        like = f'%{query_str}%'
        jobs_q = jobs_q.filter(
            or_(
                Job.title.ilike(like),
                Job.description.ilike(like),
                Job.skills_required.ilike(like),
            )
        )

    if location:
        jobs_q = jobs_q.filter(Job.location.ilike(f'%{location}%'))

    if category_id:
        jobs_q = jobs_q.filter_by(category_id=category_id)

    if job_type:
        jobs_q = jobs_q.filter_by(job_type=job_type)

    if exp_level:
        jobs_q = jobs_q.filter_by(experience_level=exp_level)

    if remote_only:
        jobs_q = jobs_q.filter_by(is_remote=True)

    # Sorting
    if sort_by == 'oldest':
        jobs_q = jobs_q.order_by(Job.created_at.asc())
    elif sort_by == 'salary_high':
        jobs_q = jobs_q.order_by(Job.salary_max.desc().nullslast())
    else:
        jobs_q = jobs_q.order_by(Job.created_at.desc())

    pagination = jobs_q.paginate(page=page, per_page=10, error_out=False)
    categories = Category.query.all()

    return render_template(
        'jobs/search.html',
        jobs=pagination.items,
        pagination=pagination,
        categories=categories,
        query_str=query_str,
        location=location,
        category_id=category_id,
        job_type=job_type,
        exp_level=exp_level,
        remote_only=remote_only,
        sort_by=sort_by,
        total=pagination.total,
    )


@main_bp.route('/job/<int:job_id>')
def job_detail(job_id):
    """Public job detail page."""
    job = Job.query.get_or_404(job_id)

    already_applied = False
    is_saved        = False

    if current_user.is_authenticated and current_user.is_seeker:
        already_applied = Application.query.filter_by(
            applicant_id=current_user.id, job_id=job_id
        ).first() is not None

        is_saved = SavedJob.query.filter_by(
            user_id=current_user.id, job_id=job_id
        ).first() is not None

    # Related jobs (same category, different listing)
    related = (
        Job.query
        .filter(Job.category_id == job.category_id, Job.id != job.id, Job.is_active == True)
        .limit(4)
        .all()
    )

    return render_template(
        'jobs/detail.html',
        job=job,
        already_applied=already_applied,
        is_saved=is_saved,
        related=related,
    )


@main_bp.route('/job/<int:job_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    """Job seeker applies to a job."""
    if not current_user.is_seeker:
        flash('Only job seekers can apply for jobs.', 'warning')
        return redirect(url_for('main.job_detail', job_id=job_id))

    job = Job.query.get_or_404(job_id)

    # Check duplicate
    existing = Application.query.filter_by(
        applicant_id=current_user.id, job_id=job_id
    ).first()
    if existing:
        flash('You have already applied for this job.', 'info')
        return redirect(url_for('main.job_detail', job_id=job_id))

    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter', '').strip()
        app = Application(
            applicant_id=current_user.id,
            job_id=job_id,
            cover_letter=cover_letter,
        )
        db.session.add(app)
        db.session.commit()
        flash('Application submitted successfully! 🎉', 'success')
        return redirect(url_for('dashboard.seeker_dashboard'))

    return render_template('jobs/apply.html', job=job)


@main_bp.route('/job/<int:job_id>/save', methods=['POST'])
@login_required
def save_job(job_id):
    """Toggle saved/bookmarked state for a job."""
    if not current_user.is_seeker:
        return jsonify({'status': 'error', 'msg': 'Not allowed'}), 403

    job = Job.query.get_or_404(job_id)
    existing = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'status': 'removed'})
    else:
        saved = SavedJob(user_id=current_user.id, job_id=job_id)
        db.session.add(saved)
        db.session.commit()
        return jsonify({'status': 'saved'})


# ── Seeker dashboard blueprint (registered separately in app.py) ──────────────
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def seeker_dashboard():
    if not current_user.is_seeker:
        return redirect(url_for('main.index'))

    applications = (
        Application.query
        .filter_by(applicant_id=current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    saved_jobs = (
        SavedJob.query
        .filter_by(user_id=current_user.id)
        .order_by(SavedJob.saved_at.desc())
        .all()
    )

    return render_template(
        'dashboard/seeker.html',
        applications=applications,
        saved_jobs=saved_jobs,
    )

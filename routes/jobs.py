"""
Jobs blueprint — thin shim; most job logic lives in main.py.
This file adds seeker dashboard endpoints under /jobs prefix.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Application, SavedJob

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/my-applications')
@login_required
def my_applications():
    if not current_user.is_seeker:
        return redirect(url_for('main.index'))

    apps = (
        Application.query
        .filter_by(applicant_id=current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return render_template('dashboard/applications.html', applications=apps)


@jobs_bp.route('/saved')
@login_required
def saved_jobs():
    if not current_user.is_seeker:
        return redirect(url_for('main.index'))

    saved = (
        SavedJob.query
        .filter_by(user_id=current_user.id)
        .order_by(SavedJob.saved_at.desc())
        .all()
    )
    return render_template('dashboard/saved_jobs.html', saved_jobs=saved)

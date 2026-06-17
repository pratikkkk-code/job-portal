"""
Database models for Job Portal Application.
Tables: User, Category, Job, Application, SavedJob
"""

from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(db.Model, UserMixin):
    """Unified user model; role determines access level."""
    __tablename__ = 'users'

    id                  = db.Column(db.Integer, primary_key=True)
    username            = db.Column(db.String(50),  unique=True, nullable=False)
    email               = db.Column(db.String(120), unique=True, nullable=False)
    password            = db.Column(db.String(255), nullable=False)
    role                = db.Column(db.String(20),  nullable=False, default='seeker')
    # 'seeker' | 'employer' | 'admin'

    # Profile fields
    full_name           = db.Column(db.String(100))
    phone               = db.Column(db.String(20))
    location            = db.Column(db.String(100))
    bio                 = db.Column(db.Text)
    resume_filename     = db.Column(db.String(200))
    skills              = db.Column(db.Text)          # comma-separated
    experience_years    = db.Column(db.Integer, default=0)

    # Employer-only fields
    company_name        = db.Column(db.String(150))
    company_description = db.Column(db.Text)
    website             = db.Column(db.String(200))

    is_verified         = db.Column(db.Boolean, default=False)
    is_active           = db.Column(db.Boolean, default=True)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    last_login          = db.Column(db.DateTime)

    # Relationships
    posted_jobs   = db.relationship('Job',         backref='employer',  lazy='dynamic',
                                    foreign_keys='Job.employer_id')
    applications  = db.relationship('Application', backref='applicant', lazy='dynamic',
                                    foreign_keys='Application.applicant_id')
    saved_jobs    = db.relationship('SavedJob',    backref='user',      lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_employer(self):
        return self.role == 'employer'

    @property
    def is_seeker(self):
        return self.role == 'seeker'


class Category(db.Model):
    """Job category (Technology, Finance, etc.)"""
    __tablename__ = 'categories'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    icon = db.Column(db.String(50), default='bi-briefcase')

    jobs = db.relationship('Job', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Job(db.Model):
    """Job listing posted by an employer."""
    __tablename__ = 'jobs'

    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(150), nullable=False)
    description      = db.Column(db.Text,        nullable=False)
    salary_min       = db.Column(db.Integer)
    salary_max       = db.Column(db.Integer)
    location         = db.Column(db.String(100), nullable=False)
    job_type         = db.Column(db.String(50),  default='Full-Time')
    # Full-Time | Part-Time | Contract | Internship | Freelance
    experience_level = db.Column(db.String(50),  default='Mid-Level')
    # Entry-Level | Mid-Level | Senior | Lead | Director
    is_remote        = db.Column(db.Boolean,     default=False)
    skills_required  = db.Column(db.Text)
    is_active        = db.Column(db.Boolean,     default=True)
    created_at       = db.Column(db.DateTime,    default=datetime.utcnow)
    deadline         = db.Column(db.DateTime)

    employer_id  = db.Column(db.Integer, db.ForeignKey('users.id'),       nullable=False)
    category_id  = db.Column(db.Integer, db.ForeignKey('categories.id'))

    applications = db.relationship('Application', backref='job', lazy='dynamic',
                                   cascade='all, delete-orphan')
    saved_by     = db.relationship('SavedJob',    backref='job', lazy='dynamic',
                                   cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Job {self.title}>'

    @property
    def salary_display(self):
        if self.salary_min and self.salary_max:
            return f'₹{self.salary_min:,} – ₹{self.salary_max:,}'
        elif self.salary_min:
            return f'₹{self.salary_min:,}+'
        return 'Negotiable'

    @property
    def application_count(self):
        return self.applications.count()


class Application(db.Model):
    """A job seeker's application to a specific job."""
    __tablename__ = 'applications'

    id           = db.Column(db.Integer, primary_key=True)
    cover_letter = db.Column(db.Text)
    status       = db.Column(db.String(30), default='Pending')
    # Pending | Reviewed | Shortlisted | Rejected | Hired
    applied_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id       = db.Column(db.Integer, db.ForeignKey('jobs.id'),  nullable=False)

    __table_args__ = (
        db.UniqueConstraint('applicant_id', 'job_id', name='unique_application'),
    )

    def __repr__(self):
        return f'<Application job={self.job_id} user={self.applicant_id}>'


class SavedJob(db.Model):
    """Bookmarked jobs for a seeker."""
    __tablename__ = 'saved_jobs'

    id       = db.Column(db.Integer, primary_key=True)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id  = db.Column(db.Integer, db.ForeignKey('jobs.id'),  nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='unique_saved_job'),
    )

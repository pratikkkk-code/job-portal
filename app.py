"""
Job Portal Web Application
Main application entry point
"""

from flask import Flask
from extensions import db, login_manager, bcrypt
from models import User
import os


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # ── Configuration ────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///jobportal.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB upload limit

    # ── Extensions ───────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_now():
        from datetime import datetime as _dt
        return {'now': _dt.utcnow()}

    # ── Blueprints ───────────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.main import main_bp, dashboard_bp
    from routes.jobs import jobs_bp
    from routes.employer import employer_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(jobs_bp,      url_prefix='/jobs')
    app.register_blueprint(employer_bp,  url_prefix='/employer')
    app.register_blueprint(admin_bp,     url_prefix='/admin')

    # ── Database init ────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    """Insert default admin + sample data if DB is empty"""
    from models import User, Job, Category
    from extensions import bcrypt

    # Seed categories
    if Category.query.count() == 0:
        categories = [
            Category(name='Technology',      icon='bi-laptop'),
            Category(name='Marketing',       icon='bi-megaphone'),
            Category(name='Finance',         icon='bi-cash-stack'),
            Category(name='Healthcare',      icon='bi-heart-pulse'),
            Category(name='Education',       icon='bi-book'),
            Category(name='Design',          icon='bi-palette'),
            Category(name='Engineering',     icon='bi-gear'),
            Category(name='Sales',           icon='bi-bar-chart'),
        ]
        db.session.add_all(categories)
        db.session.commit()

    # Seed admin user
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@jobportal.com',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin',
            full_name='Portal Administrator',
            is_verified=True,
        )
        db.session.add(admin)

    # Seed a demo employer
    if not User.query.filter_by(email='employer@demo.com').first():
        employer = User(
            username='techcorp',
            email='employer@demo.com',
            password=bcrypt.generate_password_hash('demo123').decode('utf-8'),
            role='employer',
            full_name='TechCorp Inc.',
            company_name='TechCorp Inc.',
            company_description='A leading technology company.',
            location='Mumbai, India',
            is_verified=True,
        )
        db.session.add(employer)
        db.session.commit()

        # Seed demo jobs
        cat_tech = Category.query.filter_by(name='Technology').first()
        cat_design = Category.query.filter_by(name='Design').first()

        demo_jobs = [
            Job(
                title='Senior Python Developer',
                description='We are looking for an experienced Python developer to join our backend team. You will design scalable REST APIs, work with Django/Flask, and mentor junior engineers.\n\nRequirements:\n• 4+ years Python experience\n• Strong knowledge of Django or Flask\n• Experience with PostgreSQL and Redis\n• Familiarity with Docker and CI/CD pipelines',
                salary_min=800000,
                salary_max=1400000,
                location='Mumbai, India',
                job_type='Full-Time',
                experience_level='Senior',
                is_remote=True,
                employer_id=employer.id,
                category_id=cat_tech.id if cat_tech else None,
                skills_required='Python, Django, Flask, PostgreSQL, Docker',
                is_active=True,
            ),
            Job(
                title='UI/UX Designer',
                description='Join our creative team to craft beautiful, user-centric digital experiences. You will work closely with product managers and engineers.\n\nRequirements:\n• 2+ years UX design experience\n• Proficiency in Figma\n• Portfolio demonstrating end-to-end design process\n• Understanding of accessibility standards',
                salary_min=500000,
                salary_max=900000,
                location='Bengaluru, India',
                job_type='Full-Time',
                experience_level='Mid-Level',
                is_remote=False,
                employer_id=employer.id,
                category_id=cat_design.id if cat_design else None,
                skills_required='Figma, Adobe XD, Prototyping, User Research',
                is_active=True,
            ),
        ]
        db.session.add_all(demo_jobs)

    db.session.commit()


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

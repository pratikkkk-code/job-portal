# JobConnect — Job Portal Web Application

A full-featured job portal built with **Flask**, **SQLite**, **Bootstrap 5**, and **Flask-Login**, supporting three user roles — Job Seekers, Employers, and Admins.

---

## ✨ Features

### Job Seekers
- Register / log in / edit profile (skills, bio, experience, resume info)
- Search jobs by keyword, location, category, job type, experience level, and remote-only
- Sort results by newest, oldest, or highest salary, with pagination
- View detailed job pages with company info and similar-job suggestions
- Apply to jobs with an optional cover letter (duplicate-apply protection)
- Save / bookmark jobs for later
- Personal dashboard showing application stats and saved jobs

### Employers
- Post new job listings (title, description, salary range, location, type, category, skills, deadline, remote flag)
- Edit, pause/activate, or delete listings
- View and manage applicants per job
- Update applicant status (Pending → Reviewed → Shortlisted → Rejected → Hired)
- Employer dashboard with job/applicant statistics

### Admin
- Platform-wide dashboard (user counts, job counts, application counts)
- Manage all users — search, filter by role, activate/deactivate, delete
- Manage all job listings — search, filter by status, delete
- Manage job categories — add/delete

### General
- Secure password hashing (Flask-Bcrypt)
- Session-based authentication (Flask-Login)
- Role-based access control on every protected route
- Responsive Bootstrap 5 UI with a custom design system (cards, badges, pagination)
- SQLite database via SQLAlchemy ORM (auto-created on first run, pre-seeded with demo data)

---

## 🛠 Tech Stack

| Layer        | Technology                          |
|--------------|--------------------------------------|
| Backend      | Python 3 / Flask (Application Factory pattern, Blueprints) |
| Database     | SQLite (via Flask-SQLAlchemy) — swappable for PostgreSQL   |
| Auth         | Flask-Login + Flask-Bcrypt           |
| Frontend     | HTML5, Bootstrap 5, Bootstrap Icons, vanilla JS |
| Templating   | Jinja2                               |

---

## 📂 Project Structure

```
job_portal/
├── app.py                  # App factory, config, blueprint registration, DB seeding
├── extensions.py           # Shared Flask extension instances (db, login_manager, bcrypt)
├── models.py               # SQLAlchemy models: User, Category, Job, Application, SavedJob
├── requirements.txt
├── routes/
│   ├── auth.py              # Register, login, logout, profile
│   ├── main.py              # Home, search, job detail, apply, save, seeker dashboard
│   ├── jobs.py               # My-applications & saved-jobs pages
│   ├── employer.py          # Post/edit/delete jobs, view & manage applicants
│   └── admin.py              # Admin dashboard, user/job/category management
├── templates/
│   ├── base.html             # Shared layout, navbar, footer, design tokens
│   ├── index.html             # Landing page
│   ├── auth/                  # login, register, profile
│   ├── jobs/                   # search, detail, apply
│   ├── dashboard/               # seeker dashboard, applications, saved jobs
│   ├── employer/                 # dashboard, post/edit job, applicants
│   └── admin/                     # dashboard, users, jobs, categories
└── static/
    ├── css/  js/  img/        # placeholders (styling is inlined in base.html)
```

---

## 🚀 Setup Instructions

### 1. Clone / extract the project
```bash
cd job_portal
```

### 2. Create a virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```
The app starts at **http://127.0.0.1:5000**. The SQLite database (`jobportal.db`) and demo data are created automatically on first run — no manual migration step required.

### 5. Log in with demo accounts

| Role     | Email                  | Password  |
|----------|--------------------------|-----------|
| Admin    | admin@jobportal.com      | admin123  |
| Employer | employer@demo.com        | demo123   |

Or click **Sign Up** to create a new Job Seeker or Employer account.

---

## 🔧 Configuration

Environment variables (optional — sensible defaults are used if omitted):

| Variable        | Purpose                              | Default                     |
|-----------------|----------------------------------------|------------------------------|
| `SECRET_KEY`    | Flask session signing key              | `dev-secret-key-change-in-prod` |
| `DATABASE_URL`  | SQLAlchemy DB URI (swap for PostgreSQL)| `sqlite:///jobportal.db`     |

To use PostgreSQL instead of SQLite:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/jobportal"
pip install psycopg2-binary
```

---

## 🗄 Database Schema

- **User** — unified table for seekers, employers, and admins (`role` column); stores profile, company, and auth fields.
- **Category** — job categories (Technology, Finance, Design, …).
- **Job** — listings posted by an employer; linked to a category and employer.
- **Application** — a seeker's application to a job; tracks `status` and `cover_letter`; unique per (applicant, job).
- **SavedJob** — bookmark relation between a seeker and a job.

---

## 📌 Notes

- All forms include both client- and server-side validation; duplicate applications/usernames/emails are blocked.
- Employers and admins cannot access or modify resources they do not own (ownership checks on every edit/delete route).
- Passwords are never stored in plain text — hashed with bcrypt.
- This project uses Flask's **Application Factory** pattern with **Blueprints** for clean separation of concerns, making it straightforward to extend (e.g., add REST API endpoints, email notifications, or resume file uploads).

---

## 📝 Possible Future Enhancements
- Resume (PDF) upload & parsing
- Email notifications on application status change
- External job API integration (e.g., Adzuna, RemoteOK)

---
Screenshots 

<img width="1792" height="997" alt="Screenshot 2026-06-17 at 1 05 57 PM" src="https://github.com/user-attachments/assets/b2491418-5170-4c52-90a8-7d4d50037b74" />
<img width="1792" height="999" alt="Screenshot 2026-06-17 at 1 09 20 PM" src="https://github.com/user-attachments/assets/f853d62c-4d89-4a56-bc6e-9f34b00a0741" />
<img width="1792" height="1000" alt="Screenshot 2026-06-17 at 1 08 57 PM" src="https://github.com/user-attachments/assets/0d2bc271-bbac-4572-a54a-f7202f659bfa" />
<img width="1790" height="993" alt="Screenshot 2026-06-17 at 1 10 30 PM" src="https://github.com/user-attachments/assets/b350979e-c5cd-4518-86fb-85c5e2b3b11b" />
<img width="1792" height="994" alt="Screenshot 2026-06-17 at 1 10 11 PM" src="https://github.com/user-attachments/assets/bea4386f-6d34-49f6-863f-19cdea694021" />
<img width="1792" height="997" alt="Screenshot 2026-06-17 at 1 09 59 PM" src="https://github.com/user-attachments/assets/a77e60a0-f1ef-47a5-a929-31dd9962a51d" />


- Advanced analytics dashboard for admins
- Deployment configs for Render / Railway / Heroku

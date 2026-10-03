# Lodestar

**A personalized, AI-assisted Learning Management System.**

A lodestar is the star sailors used to navigate by — the name reflects the
core idea of the platform: every student gets their own plotted path,
generated from their skill assessments, quiz performance, and interests,
rather than a fixed syllabus.

Built with Django (SQLite, Django's built-in auth — no DRF/JWT/Celery/Redis)
for a college capstone / portfolio-scale project.

---

## Stack

- **Backend:** Django 5.x, Python 3.10+
- **Database:** SQLite (zero setup)
- **Auth:** Django's built-in session auth, custom `User` model with roles
- **API:** Hand-rolled `JsonResponse` endpoints (no DRF) under `/api/`
- **Frontend:** Django templates, hand-written CSS design system (no build step)
- **AI/recommendations:** A transparent, explainable rule-based scoring engine
  (`apps/recommendations/engine.py`) combining skill-based, content-based and
  performance-based signals. Automatically upgrades to scikit-learn TF-IDF
  course-similarity if scikit-learn is installed, but works with zero extra
  dependencies if it isn't.

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database and apply migrations
python manage.py makemigrations users core courses quizzes recommendations analytics notifications gamification administration
python manage.py migrate

# 4. Seed demo data (categories, skills, users, courses, lessons, a skill assessment)
python manage.py seed_data

# 5. Run the dev server
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**.

### Demo accounts (created by `seed_data`)

| Role       | Username     | Password        |
|------------|--------------|------------------|
| Admin      | `admin`      | `admin123`       |
| Instructor | `instructor` | `instructor123`  |
| Student    | `student`    | `student123`     |

The admin account is also a Django superuser, so `/admin/` works immediately.

## Project structure

```
config/                  Django project settings, root urls, wsgi/asgi
apps/
  users/                 Custom User model, StudentProfile, InstructorProfile, auth
  core/                  Public pages (home/about/contact/FAQ), lightweight JSON API
  courses/                Category, Skill, Course, Lesson, LearningMaterial, Enrollment
  quizzes/                Quiz, Question, Answer, QuizResult, grading, skill assessments
  recommendations/        StudentSkill, Recommendation, LearningPath + the recommendation engine
  analytics/               StudentProgress + dashboard aggregation services
  dashboard/               Role-based dashboard routing (student/instructor/admin)
  notifications/           Notification model + in-app notification service
  gamification/            Badge, StudentBadge, Achievement, streaks, leaderboard
  administration/          Admin console: instructor approval, user/course management
templates/                All HTML templates, organized by app
static/css/style.css      The Lodestar design system (single stylesheet)
```

## How the recommendation engine works

1. **Skill-based** — every quiz question is tagged with a `Skill`. After each
   quiz attempt, `apps/recommendations/engine.py::update_skills_from_quiz_result`
   rolls per-question correctness into a `StudentSkill.proficiency_percent`
   (a weighted rolling average, so recent attempts count more without
   discarding history).
2. **Content-based** — a student's declared interests and preferred domains
   (free text on `StudentProfile`) are matched against course titles,
   categories and skills.
3. **Performance-based** — recent quiz score trends and course popularity are
   used as tie-breakers.

Every `Recommendation` a student sees is stored with a `reason` (weak-skill /
interest-match / next-in-path / popular-in-domain) and a human-readable
`explanation` — nothing is a black box.

`generate_learning_path` builds an ordered, per-domain sequence of courses,
auto-marking a course "completed" if the student is already strong in all of
its skills, so learners aren't told to redo things they've already mastered.

## Design system

The visual identity ("Lodestar") is a deep-indigo night sky with gold and
teal accents, `Fraunces` (display) + `Sora` (body) typefaces, and a
constellation motif used for learning-path progress (`ls-trail` /
`ls-constellation` in `static/css/style.css`) instead of a generic progress
bar. All styling lives in that one file — no CSS framework, no build step.

## Notes for local development

- No network access was available while building this project, so the code
  was hand-written rather than scaffolded/tested via `django-admin` — run the
  migrate step above to catch anything environment-specific.
- File uploads (course thumbnails, profile pictures) are stored under `media/`
  and served by Django's dev server only when `DEBUG=True`.
- `SECRET_KEY` in `config/settings.py` is a placeholder — change it before any
  real deployment.

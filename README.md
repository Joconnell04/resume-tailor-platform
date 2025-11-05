# MyApply Resume Tailor

This is the class project where I’m building a lightweight resume tailoring portal on top of Django. Job seekers can track roles they’re interested in, store a structured "experience graph," and run an OpenAI-powered workflow that spits out tailored resume bullets. Everything runs against MySQL and a Celery worker so the browser never blocks while OpenAI does its thing.

## What lives in each app?

- **accounts** – custom `User` model with roles plus token/word usage counters so I can rate-limit OpenAI consumption.
- **profiles** – simple CRUD for the user’s personal info and links that end up on the resume preview.
- **experience** – the “experience graph” manager. Users edit job, project, education, and volunteer entries through well-validated forms that write to JSON in MySQL. Sorting, validation, and conversions all live in `experience/services.py`.
- **jobs** – lets a user paste a job description, drop a posting URL, or do both. Stores parsing metadata so the tailoring service can reuse it.
- **tailoring** – asynchronous pipeline: snapshots the job + experience data, enqueues a Celery task, calls the OpenAI Responses API, and stores the generated bullets/sections/suggestions with debug logs.
- **maps** – placeholder for Mapbox commute calculations (API key wiring is already in settings but the feature is still a stub).
- **myapply** – the project config plus shared templates (`base.html`, dashboard, login) and Celery bootstrap.

## Stack + infrastructure

- **Backend**: Django 4.2, Python 3.10+, Django REST Framework for the API, Celery 5 with Redis for background jobs.
- **Database**: MySQL only. There’s no SQLite fallback anywhere, so make sure you have a running MySQL 8 instance for dev and tests.
- **AI**: OpenAI Responses API (model defaults to `gpt-4.1-mini`). The service handles prompt building, requirement extraction, and output parsing.
- **Other services**: Redis (broker + result backend), optional Mapbox token waiting for the maps feature.
- **Frontend**: Django template system with all templates scoped to each app, plus a shared CSS file in `static/css/style.css`.

## Local setup

1. Clone the repo and create a virtualenv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure MySQL is running and create a database/user. For example:
   ```sql
   CREATE DATABASE myapply CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'myapply_user'@'localhost' IDENTIFIED BY 'choose_a_password';
   GRANT ALL PRIVILEGES ON myapply.* TO 'myapply_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
4. Copy `.env.example` to `.env` and fill in the blanks for `DJANGO_SECRET_KEY`, MySQL creds, `OPENAI_API_KEY`, `OPENAI_MODEL`, and the Redis URLs. No SQLite settings are honored, so leave those out.
5. Run migrations and create a superuser:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
6. Start Redis (local default is fine):
   ```bash
   redis-server
   ```
7. In separate terminals, launch Celery and Django:
   ```bash
   celery -A myapply worker -l info
   python manage.py runserver
   ```
8. Visit `http://127.0.0.1:8000/`, log in, and you’re set.

### Running tests

Tests expect a reachable MySQL database and any required env vars. Run everything with:
```bash
python manage.py test
```

## Feature highlights

### Experience manager
- Four supported types (work, education, project, volunteer) with validation baked into `ExperienceService`.
- Glassmorphism card UI, dynamic achievements, and comma-separated skill tags.
- Everything saved to the `ExperienceGraph` JSON field, sorted and sanitized before it touches MySQL.
- When a location is provided (and `MAPBOX_TOKEN` is set) the service forward-geocodes it with Mapbox and stores latitude/longitude for future isochrone calculations.

### Job tracking
- Single form that accepts a posting URL, raw description text, or both.
- Metadata fields (company, location, parsed_requirements, etc.) live on the `JobPosting` model, so the tailoring task can reuse them without re-scraping.

### Tailoring workflow
- Creates a `TailoringSession` with snapshots of the job data and the user’s experience graph.
- Users choose sections, tone, bullet counts, and whether to include summaries or cover letters before submitting.
- Celery task scrapes the URL (if provided), merges content, builds a structured OpenAI prompt, and persists the result (sections, bullets, summary, suggestions, optional cover letter).
- Token usage and word counts are recorded back onto the user for quota tracking.
- Session detail page shows statuses, run IDs, token stats, generated content, and a collapsible debug log for troubleshooting.
- If Redis isn’t running when you kick off a session, the view falls back to executing the task synchronously and lets you know with a banner.

### Dashboard + profiles
- Dashboard pulls recent jobs, tailoring sessions, and token counts.
- Profile editor keeps basic resume contact info in sync with what the tailoring output expects.

### API surface
- REST endpoints for authentication, experience graph CRUD, job postings, tailoring sessions, and profiles (see `myapply/urls.py` + app `frontend_urls.py`).
- Token auth + session auth are both enabled so the web UI and API clients can coexist.

## Environment variables cheat sheet

```
DJANGO_SECRET_KEY=change-me
DEBUG=True
DB_NAME=myapply
DB_USER=myapply_user
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=3306
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
MAPBOX_TOKEN=optional
LOG_LEVEL=INFO
```

## Why no SQLite?

The project relies on JSON columns, MySQL-specific ordering, and long-running Celery jobs that expect a real database connection. Tests and dev use the same MySQL instance so that I don’t get surprised by behavior differences later. If MySQL isn’t available, the app just won’t boot.

## Old scripts & docs

Everything that used to live in `EXPERIENCE_FEATURE.md` is folded into this README. The legacy shell test `test_experience_service.py` has been dropped now that automated tests cover the service layer.

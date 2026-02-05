# MyApply Resume Tailor

This is my class project where I built a Django-based resume tailoring platform. The idea is to help job seekers create better, more targeted resumes by leveraging AI to match their experience with specific job requirements.

## What This Project Does

At its core, this platform takes your work history and education (stored as an "experience graph"), analyzes a job posting you're interested in, and generates customized resume content that highlights the most relevant parts of your background. Instead of sending the same generic resume everywhere, you can quickly tailor your application to each role.

The system uses OpenAI's GPT models to intelligently select which experiences to emphasize, write achievement bullets, check for accuracy, and even generate cover letters. Everything runs asynchronously using Django-Q, so the interface stays responsive while AI does its work in the background.

## How It Works

Here's the basic workflow:

1. **Build Your Experience Graph** - You enter your jobs, education, projects, and volunteer work through structured forms. The system validates and stores everything as JSON in MySQL.

2. **Add Job Postings** - Paste a job description or provide a URL to a posting. If you provide a URL, the system can fetch the full posting automatically using OpenAI's web search capabilities.

3. **Kick Off a Tailoring Session** - Select which resume sections you want, how many bullets per section, and the "stretch level" (how creative the AI should be). The system creates a snapshot of your data and queues a background task.

4. **AI Processing** - The background worker does several things:
   - Extracts key requirements from the job posting (skills, certifications, keywords)
   - Scores all your experiences against those requirements
   - Selects the most relevant snippets from your history
   - Generates resume bullets using OpenAI, structured as JSON for reliability
   - Runs guardrail checks to ensure bullets don't overstate your qualifications
   - Calculates an ATS compatibility score
   - Optionally generates a cover letter

5. **Review Results** - View the generated content, ATS score, suggestions for improvement, and detailed debugging info. You can iterate by adjusting parameters and running new sessions.

The system tracks token usage and word counts so you can stay within usage quotas.

## Project Structure

The codebase is organized into Django apps, each handling a specific domain:

- **accounts** - Custom user model with token/word usage tracking for rate limiting
- **profiles** - Personal information and contact details for resume headers
- **experience** - The experience graph manager. Handles CRUD operations for jobs, education, projects, and volunteer work
- **jobs** - Job posting storage and parsing
- **tailoring** - The core AI pipeline. Orchestrates OpenAI calls, guardrail validation, and ATS scoring
- **maps** - Optional Mapbox integration for commute calculations (still in development)
- **myapply** - Main project configuration, shared templates, and Django-Q setup

## Technology Stack

**Backend:**
- Django 4.2 with Python 3.10+
- Django REST Framework for API endpoints
- Django-Q2 for background job processing
- MySQL for data storage

**AI:**
- OpenAI Responses API (defaults to gpt-4o-mini)
- JSON mode for structured, parseable output
- Web search tool for fetching job postings from URLs

**Frontend:**
- Django templates with app-specific template directories
- Shared CSS in the static folder

**Background Tasks:**
- Django-Q2 uses MySQL as the task queue (no Redis needed)
- Works seamlessly on PythonAnywhere and similar platforms

## Getting Started

### Prerequisites

You'll need MySQL 8 running locally. This project doesn't support SQLite because it relies on MySQL-specific JSON column features.

### Setup Steps

1. Clone the repository and create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up MySQL database:
   ```sql
   CREATE DATABASE myapply CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'myapply_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON myapply.* TO 'myapply_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your `DJANGO_SECRET_KEY` (generate one if needed)
   - Add your MySQL credentials
   - Add your `OPENAI_API_KEY` from OpenAI's platform
   - Optionally add `MAPBOX_TOKEN` if you want to use the maps feature

5. Run database migrations:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. Start the services in separate terminal windows:
   ```bash
   # Terminal 1: Django-Q worker for background tasks
   python manage.py qcluster
   
   # Terminal 2: Django development server
   python manage.py runserver
   ```

7. Open your browser to `http://127.0.0.1:8000/` and log in.

### Running Tests

Make sure your test database is configured and MySQL is running:
```bash
python manage.py test
```

## Key Features

### Experience Manager

The experience graph stores four types of entries: work experience, education, projects, and volunteer work. Each entry includes structured fields like dates, achievements, and skills. The interface uses a card-based design, and everything is validated before saving to ensure data quality.

If you provide location information and have a Mapbox token configured, the system can geocode locations and store coordinates for future distance calculations.

### Job Tracking

You can add jobs by pasting a URL, raw description text, or both. The system parses and stores metadata like company name, location, and requirements. This data is reused across multiple tailoring sessions without re-scraping.

The job detail pages show all related tailoring sessions, so you can track your attempts over time and see which parameters worked best.

### Tailoring Workflow

This is where the magic happens. When you create a tailoring session:

1. The system takes a snapshot of the current job data and your complete experience graph
2. It builds a job profile by extracting requirements into categories (required skills, preferred skills, certifications, etc.)
3. Each experience in your graph gets scored based on how well it matches the job requirements
4. The top-scoring experiences are sent to OpenAI as concise summaries (not full text dumps)
5. OpenAI generates resume bullets in a structured JSON format
6. A second pass validates each bullet against your actual experience to prevent hallucinations
7. Failed bullets are regenerated with stricter instructions
8. The system calculates an ATS compatibility score
9. If requested, a cover letter is generated using the same vetted experiences

The OpenAI Responses API is used throughout with JSON mode enabled whenever possible. This ensures the output is machine-parseable without issues from markdown formatting or other inconsistencies.

All token usage is tracked and logged, both for debugging and quota management. Session detail pages show everything: generated content, ATS scores, guardrail findings, token costs, and a full debug log.

### ATS Scoring

The system analyzes how well your resume matches the job posting by looking at:
- Required skills coverage (weighted heavily)
- Overall keyword matching
- Preferred skills and bonus qualifications

The goal is to hit 85%+ compatibility. The UI shows specific suggestions if you're below that threshold, like which required skills are missing or where to add metrics.

### API Access

All major functionality is available through REST endpoints, so you could build a custom frontend or integrate with other tools. The API supports both token authentication and session authentication.

## Environment Variables

Here's what you need in your `.env` file:

```
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=myapply
DB_USER=myapply_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
TAILORING_PENDING_TIMEOUT_MINUTES=5
TAILORING_PROCESSING_TIMEOUT_MINUTES=15
MAPBOX_TOKEN=optional-for-maps-feature
LOG_LEVEL=INFO
```

Note that Redis/Celery variables are no longer needed since the migration to Django-Q.

## Design Decisions

### Why MySQL Instead of SQLite?

This project uses MySQL-specific JSON column features and ORM methods. I wanted to avoid subtle bugs that only show up in production, so development and testing both use MySQL. If MySQL isn't available, the app won't start.

### Why Django-Q Instead of Celery?

Originally this used Celery with Redis as a broker. I switched to Django-Q2 because:
- No external dependencies (uses MySQL for task queuing)
- Simpler to deploy on platforms like PythonAnywhere
- Built-in admin integration for monitoring
- One less service to manage and configure

### How Guardrails Work

After OpenAI generates resume bullets, a second AI pass checks each one against the original experience snippet. Bullets that overstate qualifications or introduce information not in your history get flagged and regenerated. This helps maintain accuracy and prevents the AI from making things up.

The "stretch level" parameter controls how creative the AI can be:
- Level 0: Very conservative, stick closely to original phrasing
- Level 1-2: Moderate creativity allowed
- Level 3: More liberal interpretation

## Using the System

### For Job Seekers

The target is an 85%+ ATS score. Here's how to get there:

1. **Complete your experience graph** - Add all relevant experiences with detailed achievements. Include metrics where possible (percentages, dollar amounts, time saved). Use industry-standard terminology.

2. **Provide complete job information** - URLs are preferred because the AI can fetch the full posting. If pasting manually, include the entire description.

3. **Check your ATS score** - After generation, look at the breakdown. Required skills typically account for 60% of the total score.

4. **Iterate based on suggestions** - The system will tell you which required skills are missing, where to add metrics, and other improvements. Address critical items first.

### For Developers

**Always Use JSON Mode:**
Set `text.format.type = "json_object"` in OpenAI API calls to prevent markdown wrapping. This is critical for reliable parsing.

**Monitor Token Usage:**
Current average is around 4,400 tokens per session. Alert if sessions regularly exceed 7,000 tokens.

**Handle Web Search Carefully:**
The OpenAI web search tool can't be used simultaneously with JSON mode. The code handles this by conditionally enabling JSON mode and using explicit instructions when web search is needed.

**Error Handling:**
Always log API errors with payload previews. JSON parsing errors should show line/column numbers to help debugging.

## Common Issues

### Tasks Stuck in Pending Status

**Symptom:** Tailoring sessions never progress beyond "pending"

**Cause:** Django-Q worker isn't running

**Fix:** Start the worker with `python manage.py qcluster` in a separate terminal

### Low ATS Scores

**Symptom:** Scores below 70%

**Cause:** Missing required skills or insufficient keyword coverage

**Fix:** Check the `missing_required_skills` field in the session output and add those skills to your experience graph

### JSON Parsing Errors

**Symptom:** "Failed to parse OpenAI JSON payload" in logs

**Cause:** Web search and JSON mode conflict, or malformed response

**Fix:** This should be handled automatically by conditional JSON mode. If it persists, check the error logs for the exact payload and line/column number.

### OpenAI Timeouts

**Symptom:** Tasks fail with timeout errors

**Cause:** Large job descriptions or slow API responses

**Fix:** Increase the timeout in Q_CLUSTER settings (the `timeout` parameter in `settings.py`)

## Deployment

### PythonAnywhere

This application is designed to work on PythonAnywhere:

1. Set up the Django-Q worker as an "Always-on task" with command:
   ```
   source /path/to/venv/bin/activate && python manage.py qcluster
   ```

2. Monitor task status in the Django admin at `/admin/django_q/`

3. There's a synchronous fallback if the worker isn't running, but it will block web requests (not ideal for production)

### Other Platforms

- **Heroku:** Add a worker dyno with `python manage.py qcluster`
- **DigitalOcean/VPS:** Run qcluster as a systemd service
- **AWS/GCP:** Deploy in a container or EC2/Compute Engine instance

No Redis or external message brokers required.

## Recent Changes

**November 2025 - Django-Q Migration:**
Replaced Celery and Redis with Django-Q2 for simpler deployment. This reduced dependencies, eliminated the need for Redis, and made the app more portable. Background tasks now use MySQL for queuing.

Also fixed an issue where OpenAI's web search tool conflicted with JSON mode. The solution was to conditionally enable JSON mode and rely on explicit instructions when web search is needed.

## Project Status

This is a student project and still under active development. The core features work well:
- Experience management
- Job tracking
- AI-powered tailoring
- ATS scoring
- Guardrail validation

The maps feature (Mapbox integration) is mostly stubbed out and not fully functional yet.

## Technical Details

The main service layer is in `tailoring/services.py`. The `AgentKitTailoringService` class orchestrates everything:

- `run_workflow()` - Main entry point
- `_build_job_profile()` - Requirement extraction
- `_collect_experience_snippets()` - Scoring and selection
- `_generate_resume_package()` - OpenAI calls and guardrails
- `_call_openai_json()` - Handles JSON mode and web search

Background tasks are defined in `tailoring/tasks.py`. The `process_tailoring_session()` function locks the session, loads data, calls the service, and persists results.

All AI-generated content is stored in `TailoringSession.output_metadata` as JSON, including bullet details, guardrail findings, section layout, and cover letter talking points.

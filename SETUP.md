# MyApply Setup Guide

Complete setup instructions for the MyApply resume tailoring platform.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- (Optional) MySQL 8.0+ if using MySQL instead of SQLite
- (Optional) virtualenv or conda for virtual environments

## Step-by-Step Setup

### 1. Install Python Dependencies

The correct package name is `djangorestframework`, not `rest_framework`:

```bash
pip install Django==4.2.7
pip install djangorestframework==3.14.0
pip install requests==2.31.0
```

Or install all at once from requirements:
```bash
pip install -r requirements.txt
```

**Note:** If using MySQL, you may need system dependencies first:
```bash
# macOS
brew install mysql pkg-config

# Ubuntu/Debian
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential

# Then install Python MySQL client
pip install mysqlclient
```

### 2. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and set your values:
```env
DJANGO_SECRET_KEY=your-unique-secret-key-here
DEBUG=True
OPENAI_API_KEY=sk-your-openai-key
MAPBOX_TOKEN=pk.your-mapbox-token

# For SQLite (default), leave DB_ENGINE empty or commented out
# For MySQL, uncomment and configure:
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=myapply
# DB_USER=root
# DB_PASSWORD=yourpassword
# DB_HOST=localhost
# DB_PORT=3306
```

### 3. Create Database Migrations

```bash
# Create migration files for all apps
python manage.py makemigrations accounts
python manage.py makemigrations profiles
python manage.py makemigrations experience
python manage.py makemigrations jobs
python manage.py makemigrations tailoring

# Or all at once:
python manage.py makemigrations
```

### 4. Apply Migrations

```bash
python manage.py migrate
```

This creates all necessary database tables including `accounts_user`.

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit:
- API: http://127.0.0.1:8000/api/
- Admin: http://127.0.0.1:8000/admin/

## MySQL-Specific Setup

### Option 1: Local MySQL

1. Install MySQL:
```bash
# macOS
brew install mysql
brew services start mysql

# Ubuntu
sudo apt-get install mysql-server
sudo systemctl start mysql
```

2. Create database:
```bash
mysql -u root -p
```

```sql
CREATE DATABASE myapply CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'myapply_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON myapply.* TO 'myapply_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

3. Update `.env`:
```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=myapply
DB_USER=myapply_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=3306
```

4. Run migrations:
```bash
python manage.py migrate
```

### Option 2: PythonAnywhere MySQL

1. In PythonAnywhere dashboard, go to "Databases" tab
2. Create a MySQL database (e.g., `username$myapply`)
3. Note the hostname (e.g., `username.mysql.pythonanywhere-services.com`)

4. Update `.env`:
```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=username$myapply
DB_USER=username
DB_PASSWORD=your_mysql_password
DB_HOST=username.mysql.pythonanywhere-services.com
DB_PORT=3306
```

## Troubleshooting

### "No module named 'rest_framework'"

The package is called `djangorestframework`:
```bash
pip install djangorestframework
```

### "accounts_user table doesn't exist"

You need to run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### MySQL Connection Error

Check:
1. MySQL service is running: `brew services list` (macOS) or `sudo systemctl status mysql` (Linux)
2. Database exists: `mysql -u root -p -e "SHOW DATABASES;"`
3. User has permissions
4. Environment variables in `.env` are correct

### ImportError for mysqlclient

Install system dependencies first:
```bash
# macOS
brew install mysql pkg-config

# Then
pip install mysqlclient
```

## Testing the API

### Get Auth Token

```bash
curl -X POST http://127.0.0.1:8000/api-auth/login/ \
  -d "username=yourusername&password=yourpassword"
```

### Create Experience Graph

```bash
curl -X PUT http://127.0.0.1:8000/api/experience/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_json": {
      "experiences": [
        {
          "title": "Software Engineer",
          "company": "Tech Corp",
          "start": "2023-01",
          "end": "2024-08",
          "skills": ["python", "django", "postgresql"],
          "achievements": [
            "Built REST APIs serving 10K+ requests/day",
            "Reduced database query time by 40%"
          ]
        }
      ]
    }
  }'
```

### Create Job Posting

```bash
curl -X POST http://127.0.0.1:8000/api/jobs/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Backend Developer",
    "company": "StartupCo",
    "raw_description": "Looking for Python developer...",
    "location_text": "Remote"
  }'
```

### Test Tailoring (will fail until AI implemented)

```bash
curl -X POST http://127.0.0.1:8000/api/tailoring/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"job_id": 1}'
```

## Next Steps

1. **Implement OpenAI Integration** in `tailoring/services.py`
2. **Implement Mapbox Integration** in `maps/services.py`
3. **Add URL Scraping** for job posting URLs
4. **Create Frontend** or use API directly
5. **Deploy to Production** (PythonAnywhere, AWS, etc.)

## Project Structure

```
resume-tailor-platform/
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── README.md             # Main documentation
├── SETUP.md              # This file
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
│
├── myapply/             # Main project settings
│   ├── settings.py      # Django configuration
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI config
│
├── accounts/            # User management
│   ├── models.py        # Custom User model
│   ├── views.py         # User API endpoints
│   ├── serializers.py   # User serialization
│   ├── permissions.py   # Access control
│   └── utils.py         # Token management
│
├── profiles/            # User profiles
│   ├── models.py        # JobSeekerProfile model
│   └── views.py         # Profile CRUD
│
├── experience/          # Experience graphs
│   ├── models.py        # ExperienceGraph model
│   ├── views.py         # Experience API
│   └── urls.py          # Experience routes
│
├── jobs/               # Job postings
│   ├── models.py       # JobPosting model
│   └── views.py        # Job CRUD
│
├── tailoring/          # AI tailoring
│   ├── models.py       # TailoringSession model
│   ├── views.py        # Tailoring API
│   └── services.py     # AI workflow (IMPLEMENT HERE)
│
└── maps/               # Mapping services
    ├── services.py     # Mapbox integration (IMPLEMENT HERE)
    ├── views.py        # Map API endpoints
    └── urls.py         # Map routes
```

## Development Workflow

1. Make changes to models → `python manage.py makemigrations` → `python manage.py migrate`
2. Test endpoints using Django REST browsable API or curl
3. Check admin interface at `/admin/`
4. Implement AI logic in `tailoring/services.py`
5. Implement map logic in `maps/services.py`

## Production Deployment

### PythonAnywhere

1. Upload code via Git or Files tab
2. Create virtual environment: `mkvirtualenv myapply --python=python3.10`
3. Install dependencies: `pip install -r requirements.txt`
4. Set up MySQL database (see above)
5. Configure web app to use `myapply.wsgi`
6. Set environment variables in WSGI file or virtualenv postactivate
7. Run migrations: `python manage.py migrate`
8. Collect static files: `python manage.py collectstatic`

### Environment Variables in Production

Never commit `.env` file. Set variables in:
- PythonAnywhere: Add to WSGI file or virtualenv
- Heroku: Use `heroku config:set`
- AWS: Use Systems Manager Parameter Store
- Docker: Use docker-compose environment section

## Security Checklist

- [ ] Change `DJANGO_SECRET_KEY` in production
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` in settings
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Set up CORS properly if building frontend
- [ ] Regular backup of database
- [ ] Monitor token usage and set reasonable quotas

## Quick Reference

### Server Info
- **URL**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/
- **API Root**: http://127.0.0.1:8000/api/

### Development Commands
```bash
# Start server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### Quick Debugging
```bash
# Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9

# Try different port
python manage.py runserver 8001

# Reset database (SQLite only)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Implementation Status

- ✅ **Enhanced .gitignore** - Comprehensive Python/Django patterns
- ✅ **MySQL Configuration** - Environment variable support
- ✅ **Database Migrations** - All tables created including accounts_user
- ✅ **AgentKit Service** - Expanded with implementation guide and helpers
- 🚧 **OpenAI Integration** - Needs OPENAI_API_KEY and implementation
- 🚧 **Mapbox Integration** - Needs MAPBOX_TOKEN and implementation
- 🚧 **URL Scraping** - Install beautifulsoup4 and implement

## Support Resources

- Django Docs: https://docs.djangoproject.com/
- DRF Docs: https://www.django-rest-framework.org/
- OpenAI API: https://platform.openai.com/docs/
- Mapbox API: https://docs.mapbox.com/

````

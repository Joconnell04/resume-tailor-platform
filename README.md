# MyApply - Resume Tailoring Platform

A Django-based platform for parsing job descriptions, matching ATS keywords, and leveraging OpenAI to generate tailored resume bullets based on a user's experience graph.

## Features

- **Custom User Management** - Role-based authentication with token quotas
- **Experience Graphs** - JSON-based storage of work history and skills
- **Job Tracking** - Parse and store job descriptions
- **AI-Powered Tailoring** - OpenAI integration for resume optimization (stub ready)
- **Location Services** - Mapbox integration for commute calculations (stub ready)
- **REST API** - Full CRUD operations with Django REST Framework
- **Web Interface** - Dark blue themed frontend with smooth animations

## Tech Stack

- Django 5.2.6
- Django REST Framework 3.16.1
- MySQL
- OpenAI API (integration ready)
- Mapbox API (integration ready)

## Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip package manager

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- Django
- djangorestframework
- mysqlclient
- requests

### 2. Configure MySQL Database

**PythonAnywhere:**
1. Go to Databases tab
2. Create MySQL database: `username$myapply`
3. Note hostname: `username.mysql.pythonanywhere-services.com`

**Local MySQL:**
```bash
# Install MySQL
brew install mysql  # macOS
sudo apt-get install mysql-server  # Ubuntu

# Start MySQL
brew services start mysql  # macOS
sudo systemctl start mysql  # Ubuntu

# Create database
mysql -u root -p
```

```sql
CREATE DATABASE myapply CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'myapply_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON myapply.* TO 'myapply_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Set Environment Variables

Create `.env` file:
```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=myapply
DB_USER=myapply_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
OPENAI_API_KEY=sk-your-openai-key
MAPBOX_TOKEN=pk-your-mapbox-token
```

**PythonAnywhere format:**
```env
DB_NAME=username$myapply
DB_USER=username
DB_HOST=username.mysql.pythonanywhere-services.com
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Start Server

```bash
python manage.py runserver
```

Visit:
- Frontend: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/

## Project Structure

```
resume-tailor-platform/
├── accounts/          # User management & authentication
├── profiles/          # Job seeker profiles
├── experience/        # Experience graph storage
├── jobs/             # Job posting management
├── tailoring/        # AI tailoring service
├── maps/             # Location/commute services
├── templates/        # Frontend HTML templates
├── static/           # CSS, JavaScript, images
└── myapply/          # Django project settings
```

## API Endpoints

### Authentication
- `POST /api-auth/login/` - Login
- `GET /api/users/me/` - Current user info

### Experience
- `GET /api/experience/` - Get experience graph
- `PUT /api/experience/` - Update experience graph

### Jobs
- `GET /api/jobs/` - List jobs
- `POST /api/jobs/` - Create job
- `GET /api/jobs/{id}/` - Job details
- `PUT /api/jobs/{id}/` - Update job
- `DELETE /api/jobs/{id}/` - Delete job

### Tailoring
- `GET /api/tailoring/` - List sessions
- `POST /api/tailoring/` - Create session
- `GET /api/tailoring/{id}/` - Session details

### Profiles
- `GET /api/profiles/` - Get profile
- `POST /api/profiles/` - Create profile
- `PUT /api/profiles/{id}/` - Update profile

## Development Workflow

```bash
# Make model changes
# Edit models.py files

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test

# Django shell
python manage.py shell
```

## PythonAnywhere Deployment

1. **Upload Code**
   - Use Git: `git clone https://github.com/yourusername/resume-tailor-platform.git`
   - Or use Files tab to upload

2. **Create Virtual Environment**
   ```bash
   mkvirtualenv myapply --python=python3.10
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup MySQL Database**
   - Create database in Databases tab
   - Note connection details

5. **Configure Environment**
   - Edit WSGI file to include environment variables
   - Or use virtualenv postactivate hook

6. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

8. **Configure Web App**
   - Set source code path
   - Set WSGI file path: `/path/to/myapply/wsgi.py`
   - Set static files: `/static/` → `/path/to/static/`
   - Reload web app

## Environment Variables (Production)

Add to PythonAnywhere WSGI file:
```python
import os
os.environ['DJANGO_SECRET_KEY'] = 'your-secret-key'
os.environ['DEBUG'] = 'False'
os.environ['DB_NAME'] = 'username$myapply'
os.environ['DB_USER'] = 'username'
os.environ['DB_PASSWORD'] = 'your-password'
os.environ['DB_HOST'] = 'username.mysql.pythonanywhere-services.com'
os.environ['OPENAI_API_KEY'] = 'sk-your-key'
os.environ['MAPBOX_TOKEN'] = 'pk-your-token'
```

## Security Checklist

- [ ] Change `DJANGO_SECRET_KEY` in production
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` in settings.py
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Regular database backups
- [ ] Monitor token usage

## Implementation Status

- ✅ Django project structure
- ✅ MySQL database configuration
- ✅ User authentication & authorization
- ✅ REST API endpoints
- ✅ Frontend with dark blue theme
- ✅ Admin interface
- 🚧 OpenAI integration (stub ready in `tailoring/services.py`)
- 🚧 Mapbox integration (stub ready in `maps/services.py`)
- 🚧 URL scraping for job descriptions

## Troubleshooting

**MySQL Connection Error:**
- Verify credentials in `.env`
- Check MySQL is running: `brew services list` or `sudo systemctl status mysql`
- Test connection: `mysql -u username -p -h hostname`

**mysqlclient Installation Fails:**
```bash
# macOS
brew install mysql pkg-config
pip install mysqlclient

# Ubuntu
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

**Port 8000 Already in Use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Migration Errors:**
```bash
# Delete migrations and start fresh
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
python manage.py makemigrations
python manage.py migrate
```

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Mapbox API](https://docs.mapbox.com/)
- [PythonAnywhere Help](https://help.pythonanywhere.com/)

## License

MIT

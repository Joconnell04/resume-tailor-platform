# Quick Start Guide - MyApply

## ✅ Setup Complete!

Your Django project is now running. Here's what you need to know:

### 🚀 Server Running
- **URL**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/
- **API Root**: http://127.0.0.1:8000/api/

### 👤 Admin Credentials
- Username: `admin`
- Email: `jt272004@gmail.com`
- Password: (the one you just set)

## 📋 What Was Fixed

1. ✅ **Enhanced .gitignore** - Comprehensive Python/Django patterns
2. ✅ **MySQL Configuration** - Environment variable support in settings.py
3. ✅ **Database Migrations** - All tables created including accounts_user
4. ✅ **AgentKit Service** - Expanded with implementation guide and helper classes
5. ✅ **Setup Documentation** - Complete SETUP.md guide created

## 🎯 Quick Commands

### Development
```bash
# Start server
python manage.py runserver

# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell
```

### Testing API Endpoints

#### 1. Login to get token
```bash
# Visit http://127.0.0.1:8000/admin/ in browser
# Or use session auth in browsable API
```

#### 2. Test User endpoint
```bash
# Get current user info
curl http://127.0.0.1:8000/api/users/me/ \
  -H "Authorization: Token YOUR_TOKEN"
```

#### 3. Create Experience Graph
```bash
curl -X PUT http://127.0.0.1:8000/api/experience/ \
  -H "Content-Type: application/json" \
  -u admin:yourpassword \
  -d '{
    "graph_json": {
      "experiences": [{
        "title": "Operations Analyst",
        "company": "Delta Air Lines",
        "start": "2024-01",
        "end": "2024-08",
        "skills": ["python", "sql", "etl"],
        "achievements": [
          "Automated reporting systems",
          "Improved data accuracy by 40%"
        ]
      }]
    }
  }'
```

#### 4. Create Job Posting
```bash
curl -X POST http://127.0.0.1:8000/api/jobs/ \
  -H "Content-Type: application/json" \
  -u admin:yourpassword \
  -d '{
    "title": "Data Analyst",
    "company": "Tech Corp",
    "raw_description": "Looking for analyst with Python and SQL skills...",
    "location_text": "Atlanta, GA"
  }'
```

#### 5. Create Profile
```bash
curl -X POST http://127.0.0.1:8000/api/profiles/ \
  -H "Content-Type: application/json" \
  -u admin:yourpassword \
  -d '{
    "location": "Atlanta, GA",
    "preferred_radius_km": 30
  }'
```

## 🔧 Next Implementation Steps

### 1. Implement OpenAI AgentKit (Priority: HIGH)

File: `tailoring/services.py`

```python
# Install OpenAI SDK
pip install openai

# Uncomment the import and implement methods:
# - run_workflow()
# - _extract_job_requirements()
# - _match_experiences()
# - _generate_tailored_content()
```

Set environment variable:
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### 2. Implement Mapbox Integration (Priority: MEDIUM)

File: `maps/services.py`

```python
# Implement methods:
# - get_isochrone()
# - calculate_distance()
```

Set environment variable:
```bash
export MAPBOX_TOKEN="pk.your-token-here"
```

### 3. Add URL Scraping (Priority: MEDIUM)

File: `tailoring/services.py`

```python
# Install dependencies
pip install beautifulsoup4

# Implement scrape_job_url() method
```

### 4. Test Tailoring Workflow

Once AI is implemented:
```bash
curl -X POST http://127.0.0.1:8000/api/tailoring/ \
  -H "Content-Type: application/json" \
  -u admin:yourpassword \
  -d '{"job_id": 1}'
```

## 📁 Project Structure Overview

```
resume-tailor-platform/
├── accounts/        # ✅ User management with roles & tokens
├── profiles/        # ✅ Job seeker profiles
├── experience/      # ✅ Experience graph storage
├── jobs/           # ✅ Job posting management
├── tailoring/      # 🚧 AI tailoring (needs OpenAI implementation)
├── maps/           # 🚧 Maps API (needs Mapbox implementation)
└── myapply/        # ✅ Project settings
```

## 🔐 MySQL Setup (Optional)

To switch from SQLite to MySQL:

1. Install MySQL:
```bash
brew install mysql
brew services start mysql
```

2. Create database:
```bash
mysql -u root -p
```
```sql
CREATE DATABASE myapply CHARACTER SET utf8mb4;
CREATE USER 'myapply_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON myapply.* TO 'myapply_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

3. Create/edit `.env`:
```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=myapply
DB_USER=myapply_user
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306
```

4. Install MySQL client:
```bash
pip install mysqlclient
```

5. Migrate:
```bash
python manage.py migrate
python manage.py createsuperuser
```

## 🎓 Learning Resources

- **Django Tutorial**: https://docs.djangoproject.com/en/4.2/intro/tutorial01/
- **DRF Tutorial**: https://www.django-rest-framework.org/tutorial/1-serialization/
- **OpenAI API**: https://platform.openai.com/docs/quickstart
- **Mapbox API**: https://docs.mapbox.com/api/search/isochrone/

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9

# Try different port
python manage.py runserver 8001
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Database errors
```bash
# Reset database (SQLite only)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 📞 Support

See `SETUP.md` for detailed setup instructions.
See `README.md` for complete project documentation.

## 🎉 You're Ready!

Everything is set up and working. The main task now is implementing the AI logic in `tailoring/services.py` and the Mapbox integration in `maps/services.py`.

Happy coding! 🚀

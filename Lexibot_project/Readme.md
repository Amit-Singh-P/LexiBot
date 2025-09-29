# LexiBots Django Setup Guide

This guide will help you set up the LexiBots AI Legal Assistant with Django backend.

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- Git
- PostgreSQL (for production) or SQLite (for development)
- Tesseract OCR (for image text extraction)

## Quick Start

### 1. Clone and Setup Project

```bash
# Create project directory
mkdir lexibots_project
cd lexibots_project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Create Django project structure
django-admin startproject config .
cd config
django-admin startapp lexibots
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang
```

**Windows:**
- Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
- Add tesseract to your PATH

### 4. Project Structure

Create the following directory structure:

```
lexibots_project/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── lexibots/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── migrations/
│   ├── management/
│   │   └── commands/
│   │       └── cleanup_files.py
│   ├── static/
│   │   └── lexibots/
│   │       └── js/
│   │           └── main.js
│   └── templates/
│       └── lexibots/
│           └── dashboard.html
├── templates/
├── static/
├── media/
├── logs/
├── requirements.txt
├── manage.py
└── .env
```

### 5. Configuration

Create a `.env` file in your project root:

```env
# Django settings
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# For production with PostgreSQL:
# DATABASE_URL=postgres://user:password@localhost:5432/lexibots_db

# File Upload
MAX_FILE_SIZE=10485760  # 10MB

# OCR Settings
TESSERACT_CMD=/usr/bin/tesseract
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/

# Email settings (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0
```

### 6. Update Django Settings

Update your `config/settings.py` with the provided settings configuration.

### 7. Update Main URLs

Update `config/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('lexibots.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 8. Database Setup

```bash
# Create and apply migrations
python manage.py makemigrations lexibots
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 9. Collect Static Files

```bash
python manage.py collectstatic
```

### 10. Create Required Directories

```bash
mkdir -p media/legal_documents
mkdir -p logs
mkdir -p static/lexibots/js
mkdir -p templates/lexibots
```

### 11. Copy Files

Copy the provided files to their respective locations:

- Copy `views.py` content to `lexibots/views.py`
- Copy `models.py` content to `lexibots/models.py`
- Copy `urls.py` content to `lexibots/urls.py`
- Copy `admin.py` content to `lexibots/admin.py`
- Copy `dashboard.html` to `templates/lexibots/dashboard.html`
- Copy `main.js` to `static/lexibots/js/main.js`
- Copy `cleanup_files.py` to `lexibots/management/commands/cleanup_files.py`

### 12. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see your LexiBots application!

## Production Deployment

### 1. Environment Setup

```bash
# Set production environment variables
export DEBUG=False
export SECRET_KEY="your-production-secret-key"
export DATABASE_URL="postgres://user:password@localhost:5432/lexibots_prod"
export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
```

### 2. Database Setup (PostgreSQL)

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb lexibots_prod
sudo -u postgres createuser lexibots_user
sudo -u postgres psql
ALTER USER lexibots_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE lexibots_prod TO lexibots_user;
\q
```

### 3. Web Server Setup (Nginx + Gunicorn)

**Install Gunicorn:**
```bash
pip install gunicorn
```

**Create Gunicorn service file** (`/etc/systemd/system/lexibots.service`):
```ini
[Unit]
Description=LexiBots gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/lexibots_project
ExecStart=/path/to/lexibots_project/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/lexibots.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Nginx configuration** (`/etc/nginx/sites-available/lexibots`):
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    client_max_body_size 10M;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path/to/lexibots_project;
    }
    
    location /media/ {
        root /path/to/lexibots_project;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/lexibots.sock;
    }
}
```

**Enable and start services:**
```bash
sudo systemctl enable lexibots
sudo systemctl start lexibots
sudo systemctl enable nginx
sudo systemctl start nginx
sudo ln -s /etc/nginx/sites-available/lexibots /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 5. Cron Jobs for Maintenance

Add to crontab (`crontab -e`):
```bash
# Clean up old files and data daily at 2 AM
0 2 * * * /path/to/lexibots_project/venv/bin/python /path/to/lexibots_project/manage.py cleanup_files --all --days=30

# Backup database weekly
0 3 * * 0 pg_dump lexibots_prod > /backups/lexibots_$(date +\%Y\%m\%d).sql
```

## API Endpoints

The application provides the following API endpoints:

### Document Management
- `POST /api/upload-document/` - Upload a legal document
- `POST /api/remove-document/` - Remove uploaded document
- `GET /api/document-stats/` - Get document statistics

### Chat System
- `POST /api/chat/` - Send a chat message
- `GET /api/chat-history/` - Get chat history
- `POST /api/feedback/` - Provide feedback on responses

### Session Management
- `POST /api/save-session/` - Save current chat session
- `POST /api/load-session/` - Load saved session
- `GET /api/saved-sessions/` - List saved sessions
- `POST /api/clear-session/` - Clear current session

### Utilities
- `POST /api/set-language/` - Change language preference
- `GET /api/search/` - Search within document content
- `GET /api/status/` - System health check
- `GET /api/export-chat/` - Export chat history as CSV

## Management Commands

### Cleanup Command
```bash
# Clean up all old data (dry run)
python manage.py cleanup_files --all --dry-run

# Clean up files older than 30 days
python manage.py cleanup_files --cleanup-files --days=30

# Clean up old sessions and analytics
python manage.py cleanup_files --cleanup-sessions --cleanup-analytics --days=7
```

### Statistics Command
```bash
# Show system statistics for last 30 days
python manage.py lexibots_utils stats --days=30

# Migrate anonymous sessions to user account
python manage.py lexibots_utils migrate-sessions --user-id=1 --session-keys session1 session2
```

## Monitoring and Logging

### Log Files
- Django logs: `logs/django.log`
- Application logs: `logs/lexibots.log`

### Health Check
Visit `/api/status/` to check system health.

### Admin Interface
Access the admin interface at `/admin/` to:
- Manage uploaded documents
- View chat sessions and messages
- Monitor analytics events
- Configure user preferences

## Security Considerations

1. **File Upload Security:**
   - Files are validated by type and size
   - Uploaded files are stored outside the web root
   - File names are sanitized

2. **CSRF Protection:**
   - All forms include CSRF tokens
   - API endpoints are protected

3. **Input Sanitization:**
   - All user inputs are escaped and validated
   - SQL injection protection via Django ORM

4. **Session Security:**
   - Secure session configuration
   - Session data is stored server-side
   - Automatic session cleanup

5. **Production Settings:**
   - Debug mode disabled
   - Secure headers enabled
   - HTTPS enforcement
   - Static file compression

## Troubleshooting

### Common Issues

#### 1. File Upload Errors
```python
# Check file permissions
sudo chown -R www-data:www-data /path/to/lexibots_project/media/
sudo chmod -R 755 /path/to/lexibots_project/media/

# Check disk space
df -h

# Check Django settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.MEDIA_ROOT)
>>> print(settings.FILE_UPLOAD_MAX_MEMORY_SIZE)
```

#### 2. OCR Issues
```bash
# Test Tesseract installation
tesseract --version
tesseract --list-langs

# Check language packs
ls /usr/share/tesseract-ocr/4.00/tessdata/

# Test OCR manually
tesseract sample_image.jpg output_text.txt
```

#### 3. Database Connection Issues
```python
# Test database connection
python manage.py dbshell

# Check database settings
python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("SELECT 1")
>>> print(cursor.fetchone())
```

#### 4. Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --clear

# Check static file settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.STATIC_ROOT)
>>> print(settings.STATIC_URL)
```

### Performance Optimization

#### 1. Database Optimization
```python
# Add database indexes (already included in models)
python manage.py makemigrations
python manage.py migrate

# Optimize queries in views
# Use select_related() and prefetch_related() for foreign keys
```

#### 2. Caching Setup
```python
# Install Redis
sudo apt-get install redis-server

# Configure in settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Use session caching
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

#### 3. File Storage Optimization
```python
# For production, consider using cloud storage
# AWS S3 configuration example:
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
AWS_S3_REGION_NAME = 'your-region'
```

### Monitoring Setup

#### 1. Error Tracking with Sentry
```python
# Install Sentry SDK
pip install sentry-sdk[django]

# Add to settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

#### 2. Application Monitoring
```bash
# Monitor with systemd
sudo systemctl status lexibots

# Check logs
sudo journalctl -u lexibots -f

# Monitor Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

#### 3. Database Monitoring
```sql
-- Monitor PostgreSQL performance
SELECT * FROM pg_stat_activity;
SELECT * FROM pg_stat_database WHERE datname = 'lexibots_prod';
```

## Backup and Recovery

### 1. Database Backup
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/lexibots"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="lexibots_prod"

mkdir -p $BACKUP_DIR

# Create database dump
pg_dump $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
```

### 2. Media Files Backup
```bash
# Sync media files to backup location
rsync -av --delete /path/to/lexibots_project/media/ /backups/lexibots/media/
```

### 3. Recovery Process
```bash
# Restore database
gunzip -c db_backup_20231201_120000.sql.gz | psql lexibots_prod

# Restore media files
rsync -av /backups/lexibots/media/ /path/to/lexibots_project/media/

# Restart services
sudo systemctl restart lexibots
```

## Testing

### 1. Unit Tests
```python
# Create test files in lexibots/tests/
# Run tests
python manage.py test lexibots

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test lexibots
coverage report
```

### 2. Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test file upload endpoint
ab -n 100 -c 10 -p test_file.pdf -T multipart/form-data http://localhost:8000/api/upload-document/

# Test chat endpoint  
ab -n 1000 -c 50 -p chat_data.json -T application/json http://localhost:8000/api/chat/
```

### 3. Security Testing
```bash
# Basic security scan
pip install bandit
bandit -r lexibots/

# Check for vulnerabilities
pip install safety
safety check
```

## Customization

### 1. Adding New Languages
```python
# Update settings.py
LEXIBOTS_SETTINGS = {
    'SUPPORTED_LANGUAGES': ['English', 'हिन्दी', 'मराठी', 'తెలుగు', 'தமிழ்'],
    'DEFAULT_LANGUAGE': 'English',
}

# Update models.py
LANGUAGE_CHOICES = [
    ('English', 'English'),
    ('हिन्दी', 'हिन्दी'),
    ('मराठी', 'मराठी'),
    ('తెలుగు', 'తెలుగు'),
    ('தமிழ்', 'தமிழ்'),
]
```

### 2. Custom AI Response Logic
```python
# Extend the _generate_ai_response method in views.py
def _generate_ai_response(user_message, document_info):
    # Add your custom AI integration here
    # Example: OpenAI GPT, Google AI, or custom ML model
    
    # For production, replace with actual AI service
    response = call_ai_service(user_message, document_info['content'])
    return response
```

### 3. Custom Document Processing
```python
# Add support for new file types
SUPPORTED_FILE_TYPES = ['pdf', 'docx', 'txt', 'rtf']

def _extract_docx_text(file_path):
    """Extract text from DOCX files"""
    from docx import Document
    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text
```

## Development Tips

### 1. Local Development Setup
```bash
# Use Django development server with auto-reload
python manage.py runserver --settings=config.settings_dev

# Enable debug toolbar
pip install django-debug-toolbar
```

### 2. Database Migrations
```bash
# Create migration for model changes
python manage.py makemigrations lexibots

# Apply specific migration
python manage.py migrate lexibots 0001

# Rollback migration
python manage.py migrate lexibots 0001

# Show migration status
python manage.py showmigrations
```

### 3. Django Shell Commands
```python
# Access Django shell
python manage.py shell

# Common debugging commands
from lexibots.models import *
from django.contrib.auth.models import User

# Check document processing
doc = LegalDocument.objects.first()
print(doc.extracted_text[:200])

# Check user sessions
sessions = ChatSession.objects.filter(is_active=True)
for session in sessions:
    print(f"{session.user} - {session.document.title}")
```

## Support and Maintenance

### 1. Regular Maintenance Tasks
- Weekly database cleanup (`cleanup_files` command)
- Monthly log rotation
- Quarterly security updates
- Annual SSL certificate renewal

### 2. Monitoring Checklist
- [ ] Server disk space > 10% free
- [ ] Database connections < 80% of max
- [ ] Error rate < 1%
- [ ] Response time < 2 seconds
- [ ] SSL certificate valid > 30 days

### 3. Version Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart lexibots
```

## API Documentation

For detailed API documentation, you can set up automatic documentation using DRF Spectacular:

```python
# Add to INSTALLED_APPS
'drf_spectacular',

# Add to settings.py
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'LexiBots API',
    'DESCRIPTION': 'AI Legal Assistant API',
    'VERSION': '1.0.0',
}

# Add to urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

Visit `/api/docs/` for interactive API documentation.

---

## License and Legal Considerations

When deploying LexiBots in production:

1. **Data Privacy**: Ensure compliance with GDPR, CCPA, and local data protection laws
2. **Legal Disclaimers**: Add appropriate disclaimers about AI-generated legal advice
3. **Terms of Service**: Implement comprehensive terms of service
4. **Audit Logging**: Enable comprehensive audit logging for legal compliance
5. **Data Retention**: Implement proper data retention and deletion policies

---

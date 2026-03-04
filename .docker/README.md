# Docker Setup for SDS Project

This directory contains Docker configuration files for running the SDS (Safety Data Sheets) Django project.

## Files

- `Dockerfile` - Development Docker image
- `Dockerfile.prod` - Production Docker image with Gunicorn
- `docker-compose.yml` - Docker Compose configuration
- `../.dockerignore` - Files to exclude from Docker builds

## Quick Start

### Development Mode

1. **Build and run with Docker Compose:**
   ```bash
   cd /app/.docker
   docker-compose up -d
   ```

2. **Access the application:**
   - Web: http://localhost:8000
   - Admin: http://localhost:8000/admin

3. **View logs:**
   ```bash
   docker-compose logs -f web
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

### Running Management Commands

**Option 1: Using the worker container**
```bash
docker-compose exec worker python manage.py <command>
```

**Option 2: Using the web container**
```bash
docker-compose exec web python manage.py <command>
```

**Examples:**
```bash
# Import files from Contabo
docker-compose exec worker python manage.py import_contabo

# Assign MD5 content
docker-compose exec worker python manage.py assign_md5_content

# Delete duplicated files
docker-compose exec worker python manage.py delete_duplicated_sds_file

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## Production Deployment

### Using Dockerfile.prod

1. **Build the production image:**
   ```bash
   docker build -f .docker/Dockerfile.prod -t sds-app:latest .
   ```

2. **Run the production container:**
   ```bash
   docker run -d \
     --name sds-prod \
     -p 8000:8000 \
     -v $(pwd)/db.sqlite3:/app/db.sqlite3 \
     sds-app:latest
   ```

### Using Docker Compose (Production)

Create a `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  web:
    build:
      context: ..
      dockerfile: .docker/Dockerfile.prod
    container_name: sds_web_prod
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - db_volume:/app/db.sqlite3
      - static_volume:/app/static
      - media_volume:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=sds.settings
      - PYTHONUNBUFFERED=1

volumes:
  db_volume:
  static_volume:
  media_volume:
```

Then run:
```bash
docker-compose -f .docker/docker-compose.prod.yml up -d
```

## Environment Variables

You can customize the deployment with environment variables:

```bash
# In docker-compose.yml or when running docker run
environment:
  - DEBUG=False
  - SECRET_KEY=your-secret-key-here
  - ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
  - DATABASE_URL=sqlite:///db.sqlite3
```

## Volume Management

### Backup Database
```bash
docker cp sds_web:/app/db.sqlite3 ./backup-$(date +%Y%m%d).sqlite3
```

### Restore Database
```bash
docker cp ./backup.sqlite3 sds_web:/app/db.sqlite3
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs web

# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```

### Permission issues
```bash
# Fix permissions on host
sudo chown -R $USER:$USER .
```

### Database locked
```bash
# Restart the container
docker-compose restart web
```

## Architecture

```
┌─────────────────────────────────────┐
│         Docker Network              │
│                                     │
│  ┌──────────┐      ┌──────────┐   │
│  │   Web    │      │  Worker  │   │
│  │ (Django) │      │ (Tasks)  │   │
│  └──────────┘      └──────────┘   │
│       │                 │          │
│       └────────┬────────┘          │
│                │                   │
│         ┌──────▼──────┐            │
│         │   SQLite    │            │
│         │  (Volume)   │            │
│         └─────────────┘            │
└─────────────────────────────────────┘
```

## Notes

- The development Dockerfile uses Django's built-in development server
- The production Dockerfile uses Gunicorn with 4 workers
- Both containers run as non-root user `appuser` for security
- Health checks are configured to monitor application status
- Volumes are used to persist data between container restarts

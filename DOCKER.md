# SDS Project - Docker Deployment Guide

Complete Docker setup for the Safety Data Sheets (SDS) Django application.

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 1.29+

## 🚀 Quick Start

### Automated Setup

Run the setup script:

```bash
./docker-setup.sh
```

This will:
- ✅ Build Docker images
- ✅ Start all services
- ✅ Run database migrations
- ✅ Collect static files

### Manual Setup

1. **Build the images:**
   ```bash
   docker-compose -f .docker/docker-compose.yml build
   ```

2. **Start the services:**
   ```bash
   docker-compose -f .docker/docker-compose.yml up -d
   ```

3. **Run migrations:**
   ```bash
   docker-compose -f .docker/docker-compose.yml exec web python manage.py migrate
   ```

4. **Access the application:**
   - Web: http://localhost:8000
   - Admin: http://localhost:8000/admin

## 📦 What's Included

### Docker Files

```
.docker/
├── Dockerfile           # Development image
├── Dockerfile.prod      # Production image with Gunicorn
├── docker-compose.yml   # Multi-service configuration
└── README.md           # Detailed documentation

.dockerignore           # Files excluded from build
Makefile               # Convenient commands
docker-setup.sh        # Automated setup script
```

### Services

- **web** - Django application (port 8000)
- **worker** - Background task runner for management commands

## 🛠️ Using Make Commands

We provide a Makefile for convenient Docker operations:

```bash
# View all available commands
make help

# Common operations
make build              # Build Docker images
make up                 # Start services
make down               # Stop services
make restart            # Restart services
make logs               # View all logs
make logs-web           # View web container logs
make shell              # Django shell
make bash               # Bash shell in web container

# Database operations
make migrate            # Run migrations
make makemigrations     # Create migrations
make createsuperuser    # Create admin user
make backup-db          # Backup database
make restore-db FILE=backup.sqlite3  # Restore database

# Management commands
make import-contabo     # Import files from Contabo S3
make assign-md5         # Process PDFs and assign MD5 content
make delete-duplicates  # Delete duplicate SDS files

# Cleanup
make clean              # Remove containers and volumes
make clean-all          # Remove everything including images
```

## 🔧 Management Commands

### Import Files from Contabo

```bash
# Using Make
make import-contabo

# Or directly
docker-compose -f .docker/docker-compose.yml exec worker python manage.py import_contabo
```

### Assign MD5 Content

```bash
# Using Make
make assign-md5

# Or directly
docker-compose -f .docker/docker-compose.yml exec worker python manage.py assign_md5_content
```

### Delete Duplicated Files

```bash
# Using Make
make delete-duplicates

# Or directly
docker-compose -f .docker/docker-compose.yml exec worker python manage.py delete_duplicated_sds_file
```

## 🌐 Production Deployment

### Option 1: Using Production Dockerfile

```bash
# Build production image
make build-prod

# Run production container
docker run -d \
  --name sds-prod \
  -p 8000:8000 \
  -v $(pwd)/db.sqlite3:/app/db.sqlite3 \
  --restart unless-stopped \
  sds-app:latest
```

### Option 2: Production Docker Compose

Create `.docker/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  web:
    build:
      context: ..
      dockerfile: .docker/Dockerfile.prod
    container_name: sds_prod
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - db_volume:/app/db.sqlite3
    environment:
      - DJANGO_SETTINGS_MODULE=sds.settings
      - DEBUG=False

volumes:
  db_volume:
```

Then deploy:

```bash
docker-compose -f .docker/docker-compose.prod.yml up -d
```

## 📊 Monitoring & Logs

### View Logs

```bash
# All services
make logs

# Specific service
docker-compose -f .docker/docker-compose.yml logs -f web
docker-compose -f .docker/docker-compose.yml logs -f worker

# Last N lines
docker-compose -f .docker/docker-compose.yml logs --tail=100 web
```

### Check Container Status

```bash
make status

# Or
docker-compose -f .docker/docker-compose.yml ps
```

## 💾 Database Management

### Backup Database

```bash
# Using Make
make backup-db

# Manual backup
docker cp $(docker-compose -f .docker/docker-compose.yml ps -q web):/app/db.sqlite3 ./backup.sqlite3
```

### Restore Database

```bash
# Using Make
make restore-db FILE=backup.sqlite3

# Manual restore
docker cp backup.sqlite3 $(docker-compose -f .docker/docker-compose.yml ps -q web):/app/db.sqlite3
docker-compose -f .docker/docker-compose.yml restart web
```

## 🔐 Security Features

- ✅ Non-root user (appuser) inside containers
- ✅ Minimal base image (python:3.11-slim)
- ✅ Health checks configured
- ✅ No sensitive data in images
- ✅ Volume-based data persistence

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose -f .docker/docker-compose.yml logs web

# Rebuild without cache
make rebuild
```

### Permission denied errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

### Port already in use

```bash
# Stop services using port 8000
sudo lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Database is locked

```bash
# Restart the web service
docker-compose -f .docker/docker-compose.yml restart web
```

## 📝 Environment Variables

You can customize the deployment with environment variables:

```yaml
# In docker-compose.yml
environment:
  - DEBUG=False
  - SECRET_KEY=your-secret-key-here
  - ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
  - AWS_ACCESS_KEY_ID=your-key
  - AWS_SECRET_ACCESS_KEY=your-secret
```

Or use a `.env` file:

```bash
# .env file
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=example.com
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│            Docker Network                   │
│                                             │
│  ┌──────────────┐      ┌──────────────┐   │
│  │     Web      │      │    Worker    │   │
│  │   (Django)   │      │  (Commands)  │   │
│  │              │      │              │   │
│  │ - Port 8000  │      │ - Background │   │
│  │ - Gunicorn   │      │ - Tasks      │   │
│  └──────┬───────┘      └──────┬───────┘   │
│         │                     │            │
│         └──────────┬──────────┘            │
│                    │                       │
│             ┌──────▼──────┐                │
│             │   Volumes   │                │
│             ├─────────────┤                │
│             │ db.sqlite3  │                │
│             │ static/     │                │
│             │ media/      │                │
│             └─────────────┘                │
└─────────────────────────────────────────────┘
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

## 📄 License

This Docker configuration is part of the SDS project.

---

**Need help?** Check the [.docker/README.md](.docker/README.md) for more detailed information.

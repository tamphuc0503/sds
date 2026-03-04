# Environment Variables in Docker

## Methods to Set Environment Variables

### 1. In Dockerfile using ENV

```dockerfile
# Static environment variables
ENV DEBUG=False
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///db.sqlite3
```

### 2. Using docker run with -e flag

```bash
# Single variable
docker run -e DEBUG=True my-image

# Multiple variables
docker run \
  -e DEBUG=True \
  -e SECRET_KEY=my-secret-key \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  my-image
```

### 3. Using docker run with --env-file

Create a `.env` file:
```bash
# .env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

Then run:
```bash
docker run --env-file .env my-image
```

### 4. In docker-compose.yml

#### Method A: Inline environment variables
```yaml
services:
  web:
    image: my-image
    environment:
      - DEBUG=False
      - SECRET_KEY=my-secret-key
      - ALLOWED_HOSTS=localhost
```

#### Method B: Using env_file
```yaml
services:
  web:
    image: my-image
    env_file:
      - .env
```

#### Method C: Using ${VARIABLE} from host
```yaml
services:
  web:
    image: my-image
    environment:
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
```

## Best Practices for SDS Project

### 1. Create .env file

Create `/app/.env`:
```bash
# Django Settings
DEBUG=False
SECRET_KEY=change-this-to-a-random-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DATABASE_URL=sqlite:///db.sqlite3

# AWS S3 Contabo Settings
AWS_ENDPOINT_URL=https://usc1.contabostorage.com
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=usc1
AWS_BUCKET_NAME=sds

# Application Settings
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### 2. Update settings.py to use environment variables

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Read from environment variables with defaults
DEBUG = os.getenv('DEBUG', 'True') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# AWS S3 Settings
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL', 'https://usc1.contabostorage.com')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_REGION = os.getenv('AWS_REGION', 'usc1')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'sds')
```

### 3. Add .env to .gitignore

```bash
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo "*.env" >> .gitignore
```

### 4. Create .env.example (template)

Create `/app/.env.example`:
```bash
# Copy this file to .env and update with your values

# Django Settings
DEBUG=False
SECRET_KEY=change-this-to-a-random-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# AWS S3 Contabo Settings
AWS_ENDPOINT_URL=https://usc1.contabostorage.com
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=usc1
AWS_BUCKET_NAME=sds
```

## Using with Docker

### Development

```bash
# Build the image
docker build -f .docker/Dockerfile -t sds-dev .

# Run with environment variables from file
docker run --env-file .env -p 8000:8000 sds-dev

# Or with individual variables
docker run \
  -e DEBUG=True \
  -e SECRET_KEY=dev-key \
  -p 8000:8000 \
  sds-dev
```

### Production

```bash
# Build production image
docker build -f .docker/Dockerfile.prod -t sds-prod .

# Run with production .env file
docker run --env-file .env.production -p 8000:8000 sds-prod
```

### Docker Compose

Update `docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build:
      context: ..
      dockerfile: .docker/Dockerfile
    container_name: sds_web
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - ../.env
    volumes:
      - ../:/app
    networks:
      - sds_network
```

Then run:
```bash
docker-compose -f .docker/docker-compose.yml up -d
```

## Security Tips

1. **Never commit .env files to git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use different .env files for different environments**
   - `.env.development`
   - `.env.staging`
   - `.env.production`

3. **Use Docker secrets for sensitive data in production**
   ```yaml
   services:
     web:
       secrets:
         - db_password
         - secret_key
   
   secrets:
     db_password:
       file: ./secrets/db_password.txt
     secret_key:
       file: ./secrets/secret_key.txt
   ```

4. **Use environment variable validation**
   ```python
   import os
   
   required_vars = ['SECRET_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
   for var in required_vars:
       if not os.getenv(var):
           raise ValueError(f"Required environment variable {var} is not set")
   ```

## Examples for SDS Project

### Example 1: Local Development
```bash
# Create .env file
cat > .env << 'EOF'
DEBUG=True
SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=*
AWS_ACCESS_KEY_ID=f35256d14c2a22f4648bce44896529d8
AWS_SECRET_ACCESS_KEY=7672dbe85d3e540b7c62ff6df5704ef3
EOF

# Run with docker-compose
docker-compose -f .docker/docker-compose.yml up -d
```

### Example 2: Production Deployment
```bash
# Create .env.production file
cat > .env.production << 'EOF'
DEBUG=False
SECRET_KEY=$(openssl rand -base64 32)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
AWS_ACCESS_KEY_ID=your-production-key
AWS_SECRET_ACCESS_KEY=your-production-secret
EOF

# Run production container
docker run --env-file .env.production -p 8000:8000 sds-prod
```

### Example 3: Override specific variables
```bash
# Use .env file but override DEBUG
docker run --env-file .env -e DEBUG=True sds-dev
```

## Checking Environment Variables

### In running container
```bash
# View all environment variables
docker exec sds_web env

# View specific variable
docker exec sds_web printenv DEBUG

# Access container shell and check
docker exec -it sds_web bash
echo $DEBUG
```

### In docker-compose
```bash
# View environment variables for a service
docker-compose -f .docker/docker-compose.yml exec web env
```

## ARG vs ENV in Dockerfile

### ARG - Build-time variables
```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ARG BUILD_DATE
LABEL build_date=${BUILD_DATE}
```

Use with:
```bash
docker build --build-arg PYTHON_VERSION=3.11 --build-arg BUILD_DATE=$(date) .
```

### ENV - Runtime variables
```dockerfile
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
```

These are available in the running container.

## Combining ARG and ENV
```dockerfile
ARG DEBUG_MODE=False
ENV DEBUG=${DEBUG_MODE}

ARG SECRET_KEY=default-key
ENV SECRET_KEY=${SECRET_KEY}
```

Build with:
```bash
docker build --build-arg DEBUG_MODE=True --build-arg SECRET_KEY=my-key .
```

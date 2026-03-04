# External SQLite Database Configuration

This guide explains how to use an external SQLite database file with Docker.

## 📁 Database Location

The SQLite database is stored **outside** the Docker container at:
```
/app/db.sqlite3
```

This file is mounted into the container at the same path.

## 🔧 How It Works

In `docker-compose.yml`, the database is mounted as a volume:

```yaml
volumes:
  - ../db.sqlite3:/app/db.sqlite3  # Host path : Container path
```

This means:
- **Host (your machine)**: `/app/db.sqlite3`
- **Container**: `/app/db.sqlite3`
- Changes in either location are reflected in both

## ✅ Benefits of External Database

1. **Data Persistence** - Data survives container restarts
2. **Easy Backup** - Simply copy `/app/db.sqlite3`
3. **Easy Access** - Can access database from host
4. **Development** - Use SQLite browser tools on host
5. **Portability** - Move database between environments

## 🚀 Setup Instructions

### First Time Setup

1. **Ensure database file exists (or will be created)**
   ```bash
   # Database will be created automatically on first run
   # Or create empty file if needed:
   touch /app/db.sqlite3
   ```

2. **Set proper permissions**
   ```bash
   chmod 664 /app/db.sqlite3
   ```

3. **Start services**
   ```bash
   cd /app/.docker
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

### Using Makefile

```bash
# Start services
make up

# Run migrations
make migrate

# Create superuser
make createsuperuser
```

## 💾 Database Operations

### Backup Database

**From Host:**
```bash
# Simple copy
cp /app/db.sqlite3 /app/backup-$(date +%Y%m%d).sqlite3

# Using tar with compression
tar -czf /app/db-backup-$(date +%Y%m%d).tar.gz /app/db.sqlite3
```

**Using Makefile:**
```bash
make backup-db
```

### Restore Database

**From Host:**
```bash
# Stop services first
docker-compose -f .docker/docker-compose.yml down

# Restore backup
cp /path/to/backup.sqlite3 /app/db.sqlite3

# Start services
docker-compose -f .docker/docker-compose.yml up -d
```

**Using Makefile:**
```bash
make down
cp backup.sqlite3 /app/db.sqlite3
make up
```

### Access Database from Host

You can use any SQLite browser/tool to access the database:

```bash
# Using sqlite3 CLI
sqlite3 /app/db.sqlite3

# Example queries
sqlite3 /app/db.sqlite3 "SELECT * FROM sds_files LIMIT 10;"
```

**Popular SQLite Tools:**
- [DB Browser for SQLite](https://sqlitebrowser.org/)
- [SQLite Studio](https://sqlitestudio.pl/)
- [DBeaver](https://dbeaver.io/)

### Export/Import Data

**Export to SQL:**
```bash
sqlite3 /app/db.sqlite3 .dump > backup.sql
```

**Import from SQL:**
```bash
sqlite3 /app/db.sqlite3 < backup.sql
```

**Export to CSV:**
```bash
sqlite3 /app/db.sqlite3 << EOF
.headers on
.mode csv
.output /app/sds_files.csv
SELECT * FROM sds_files;
.quit
EOF
```

## 🔐 Security & Permissions

### File Permissions

The database file should be:
- **Readable** by the container user (appuser)
- **Writable** by the container user (appuser)

```bash
# Check permissions
ls -l /app/db.sqlite3

# Fix permissions if needed
chmod 664 /app/db.sqlite3
chown $USER:$USER /app/db.sqlite3
```

### Container User

The Dockerfile creates a non-root user `appuser` (UID 1000):

```dockerfile
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
```

If you have permission issues:
```bash
# Fix ownership
sudo chown 1000:1000 /app/db.sqlite3
```

## 🐛 Troubleshooting

### Database Locked Error

**Cause:** Multiple processes accessing the database simultaneously

**Solution:**
```bash
# Restart containers
docker-compose -f .docker/docker-compose.yml restart

# Or check for locks
lsof /app/db.sqlite3
```

### Permission Denied Error

**Cause:** Container user doesn't have write access

**Solution:**
```bash
# Fix permissions
chmod 664 /app/db.sqlite3
chown 1000:1000 /app/db.sqlite3

# Restart containers
docker-compose -f .docker/docker-compose.yml restart
```

### Database Not Found

**Cause:** Database file doesn't exist and migrations haven't run

**Solution:**
```bash
# Ensure file exists (Django will create it)
touch /app/db.sqlite3
chmod 664 /app/db.sqlite3

# Run migrations
docker-compose -f .docker/docker-compose.yml exec web python manage.py migrate
```

### Cannot Access from Host

**Cause:** Database is locked by container or permissions issue

**Solution:**
```bash
# Stop containers temporarily
docker-compose -f .docker/docker-compose.yml down

# Access database
sqlite3 /app/db.sqlite3

# Restart containers
docker-compose -f .docker/docker-compose.yml up -d
```

## 📊 Monitoring Database

### Check Database Size

```bash
# From host
du -h /app/db.sqlite3

# From container
docker-compose -f .docker/docker-compose.yml exec web ls -lh /app/db.sqlite3
```

### Database Statistics

```bash
sqlite3 /app/db.sqlite3 << EOF
.headers on
.mode column

-- Table list
.tables

-- Row counts
SELECT 'sds_files' as table_name, COUNT(*) as count FROM sds_files;

-- Database size
SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();
.quit
EOF
```

## 🔄 Migration to Production

When moving to production, you might want to:

1. **Switch to PostgreSQL/MySQL** for better concurrency
2. **Use external volume** for better management
3. **Set up automated backups**

Example with PostgreSQL:

```yaml
services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=sds
      - POSTGRES_USER=sds_user
      - POSTGRES_PASSWORD=secure_password

volumes:
  postgres_data:
```

## 📝 Best Practices

1. ✅ **Regular Backups** - Backup before major operations
2. ✅ **Version Control** - Don't commit `db.sqlite3` to git
3. ✅ **Test Restores** - Verify backups work
4. ✅ **Monitor Size** - SQLite has practical limits
5. ✅ **Proper Permissions** - Ensure container can write
6. ✅ **Stop Before Backup** - Stop containers for consistent backup

## 🔗 Related Files

- `docker-compose.yml` - Volume mount configuration
- `.dockerignore` - Excludes db.sqlite3 from builds
- `settings.py` - Database configuration
- `Makefile` - Backup/restore commands

## 💡 Quick Commands Reference

```bash
# Backup
make backup-db
# or
cp /app/db.sqlite3 /app/backup-$(date +%Y%m%d).sqlite3

# Restore
make down
cp backup.sqlite3 /app/db.sqlite3
make up

# Access
sqlite3 /app/db.sqlite3

# Check size
du -h /app/db.sqlite3

# View tables
sqlite3 /app/db.sqlite3 ".tables"

# Export
sqlite3 /app/db.sqlite3 .dump > backup.sql
```

---

**Note:** The database file is at `/app/db.sqlite3` on both the host and in the container, making it easy to access and manage!

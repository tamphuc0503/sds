#!/bin/bash
# Setup external SQLite database for Docker

set -e

DB_PATH="/app/db.sqlite3"
DB_DIR="/app"

echo "=================================="
echo "  External Database Setup"
echo "=================================="
echo ""

# Check if database file exists
if [ -f "$DB_PATH" ]; then
    echo "✓ Database file exists: $DB_PATH"
    
    # Check file size
    SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo "  Size: $SIZE"
    
    # Check permissions
    PERMS=$(stat -c "%a" "$DB_PATH" 2>/dev/null || stat -f "%OLp" "$DB_PATH" 2>/dev/null)
    echo "  Permissions: $PERMS"
    
else
    echo "⚠ Database file does not exist"
    echo "  Creating: $DB_PATH"
    
    # Create database file
    touch "$DB_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✓ Database file created"
    else
        echo "✗ Failed to create database file"
        exit 1
    fi
fi

# Set proper permissions
echo ""
echo "Setting proper permissions..."
chmod 664 "$DB_PATH"

if [ $? -eq 0 ]; then
    echo "✓ Permissions set to 664 (rw-rw-r--)"
else
    echo "⚠ Warning: Could not set permissions (you may need sudo)"
fi

# Check if running in container
if [ -f "/.dockerenv" ]; then
    echo ""
    echo "✓ Running inside Docker container"
    OWNER="appuser:appuser"
else
    echo ""
    echo "✓ Running on host machine"
    OWNER="$USER:$USER"
fi

echo ""
echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "Database location: $DB_PATH"
echo "Recommended owner: $OWNER"
echo ""
echo "Next steps:"
echo "  1. Start Docker services: make up"
echo "  2. Run migrations: make migrate"
echo "  3. Create superuser: make createsuperuser"
echo ""

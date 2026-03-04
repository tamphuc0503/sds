#!/bin/bash
# Docker setup script for SDS project

set -e

echo "======================================"
echo "  SDS Project Docker Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo -e "${GREEN}✓ Docker Compose is installed${NC}"
echo ""

# Build images
echo -e "${YELLOW}Building Docker images...${NC}"
cd "$(dirname "$0")"
docker-compose -f .docker/docker-compose.yml build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
else
    echo -e "${RED}✗ Failed to build Docker images${NC}"
    exit 1
fi

echo ""

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose -f .docker/docker-compose.yml up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Services started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

echo ""

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f .docker/docker-compose.yml exec -T web python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations completed${NC}"
else
    echo -e "${YELLOW}⚠ Migrations may have failed (this might be okay if database exists)${NC}"
fi

echo ""

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
docker-compose -f .docker/docker-compose.yml exec -T web python manage.py collectstatic --noinput

echo ""

echo "======================================"
echo -e "${GREEN}  Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Your SDS application is now running!"
echo ""
echo "Access the application at: http://localhost:8000"
echo ""
echo "Useful commands:"
echo "  View logs:           docker-compose -f .docker/docker-compose.yml logs -f"
echo "  Stop services:       docker-compose -f .docker/docker-compose.yml down"
echo "  Restart services:    docker-compose -f .docker/docker-compose.yml restart"
echo "  Create superuser:    docker-compose -f .docker/docker-compose.yml exec web python manage.py createsuperuser"
echo ""
echo "Or use the Makefile:"
echo "  make logs           - View logs"
echo "  make down           - Stop services"
echo "  make restart        - Restart services"
echo "  make createsuperuser - Create Django admin user"
echo "  make help           - Show all available commands"
echo ""

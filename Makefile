.PHONY: help build up down restart logs shell migrate createsuperuser clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose -f .docker/docker-compose.yml build

build-prod: ## Build production Docker image
	docker build -f .docker/Dockerfile.prod -t sds-app:latest .

up: ## Start all services
	docker-compose -f .docker/docker-compose.yml up -d

down: ## Stop all services
	docker-compose -f .docker/docker-compose.yml down

restart: ## Restart all services
	docker-compose -f .docker/docker-compose.yml restart

logs: ## Show logs
	docker-compose -f .docker/docker-compose.yml logs -f

logs-web: ## Show web container logs
	docker-compose -f .docker/docker-compose.yml logs -f web

logs-worker: ## Show worker container logs
	docker-compose -f .docker/docker-compose.yml logs -f worker

shell: ## Access Django shell in web container
	docker-compose -f .docker/docker-compose.yml exec web python manage.py shell

bash: ## Access bash in web container
	docker-compose -f .docker/docker-compose.yml exec web bash

bash-worker: ## Access bash in worker container
	docker-compose -f .docker/docker-compose.yml exec worker bash

migrate: ## Run database migrations
	docker-compose -f .docker/docker-compose.yml exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker-compose -f .docker/docker-compose.yml exec web python manage.py makemigrations

createsuperuser: ## Create Django superuser
	docker-compose -f .docker/docker-compose.yml exec web python manage.py createsuperuser

collectstatic: ## Collect static files
	docker-compose -f .docker/docker-compose.yml exec web python manage.py collectstatic --noinput

# Management commands
import-contabo: ## Run import_contabo management command
	docker-compose -f .docker/docker-compose.yml exec worker python manage.py import_contabo

assign-md5: ## Run assign_md5_content management command
	docker-compose -f .docker/docker-compose.yml exec worker python manage.py assign_md5_content

delete-duplicates: ## Run delete_duplicated_sds_file management command
	docker-compose -f .docker/docker-compose.yml exec worker python manage.py delete_duplicated_sds_file

# Database operations
backup-db: ## Backup database
	docker cp $$(docker-compose -f .docker/docker-compose.yml ps -q web):/app/db.sqlite3 ./db-backup-$$(date +%Y%m%d-%H%M%S).sqlite3
	@echo "Database backed up to db-backup-$$(date +%Y%m%d-%H%M%S).sqlite3"

restore-db: ## Restore database (usage: make restore-db FILE=backup.sqlite3)
	docker cp $(FILE) $$(docker-compose -f .docker/docker-compose.yml ps -q web):/app/db.sqlite3
	@echo "Database restored from $(FILE)"

# Cleanup
clean: ## Remove containers, volumes, and images
	docker-compose -f .docker/docker-compose.yml down -v
	docker system prune -f

clean-all: ## Remove everything including images
	docker-compose -f .docker/docker-compose.yml down -v --rmi all
	docker system prune -af

# Testing
test: ## Run tests
	docker-compose -f .docker/docker-compose.yml exec web python manage.py test

# Development helpers
rebuild: ## Rebuild and restart services
	docker-compose -f .docker/docker-compose.yml down
	docker-compose -f .docker/docker-compose.yml build --no-cache
	docker-compose -f .docker/docker-compose.yml up -d

status: ## Show container status
	docker-compose -f .docker/docker-compose.yml ps

# Production
deploy-prod: build-prod ## Deploy production version
	docker run -d \
		--name sds-prod \
		-p 8000:8000 \
		-v $$(pwd)/db.sqlite3:/app/db.sqlite3 \
		--restart unless-stopped \
		sds-app:latest

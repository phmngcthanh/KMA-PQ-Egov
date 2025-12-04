# Makefile for E-Government PKI System
# Quick commands for development and deployment

.PHONY: help dev prod stop logs clean migrate shell db-shell backup test

# Default target
help:
	@echo "E-Government PKI System - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make stop         - Stop all containers"
	@echo "  make logs         - View container logs"
	@echo "  make clean        - Stop and remove all containers and volumes"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make shell        - Open Django shell"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo "  make backup       - Backup database"
	@echo "  make superuser    - Create superuser"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build production images"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run tests"

# Development
dev:
	docker-compose up -d --build
	@echo ""
	@echo "Development environment started!"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Admin:    http://localhost:8000/admin"

stop:
	docker-compose down
	docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

clean:
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
	@echo "All containers and volumes removed"

# Database
migrate:
	docker-compose exec backend python manage.py migrate

makemigrations:
	docker-compose exec backend python manage.py makemigrations

shell:
	docker-compose exec backend python manage.py shell

db-shell:
	docker-compose exec db psql -U pnthanh -d chinhquyendt

superuser:
	docker-compose exec backend python manage.py createsuperuser

backup:
	@mkdir -p backups
	docker-compose exec db pg_dump -U pnthanh chinhquyendt > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/"

restore:
	@echo "Usage: docker-compose exec -T db psql -U pnthanh chinhquyendt < backups/your_backup.sql"

# Production
prod:
	docker-compose -f docker-compose.prod.yml up -d --build
	@echo ""
	@echo "Production environment started!"
	@echo "  Application: http://localhost"

prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

prod-migrate:
	docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

prod-superuser:
	docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Testing
test:
	docker-compose exec backend python manage.py test

test-coverage:
	docker-compose exec backend coverage run manage.py test
	docker-compose exec backend coverage report

# Utilities
collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

check:
	docker-compose exec backend python manage.py check

# Docker utilities
ps:
	docker-compose ps

images:
	docker images | grep pki

prune:
	docker system prune -f
	docker volume prune -f

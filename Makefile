.PHONY: help up down build logs test test-backend test-frontend lint lint-backend lint-frontend typecheck clean restart migrate health

help: ## Show this help message
	@echo "DataAir Makefile"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "  %-20s %s\n", "target", "description"} /^$$/ {next} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down -v

build: ## Build all services
	docker compose build --no-cache

logs: ## View logs from all services
	docker compose logs -f

restart: ## Restart all services
	docker compose restart

migrate: ## Run database migrations
	docker compose exec backend alembic upgrade head

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	docker compose exec backend pytest tests/ -v

test-frontend: ## Run frontend tests
	cd frontend && CI=true npx jest --ci

lint: lint-backend lint-frontend ## Lint backend and frontend

lint-backend: ## Lint the backend with ruff
	ruff check backend tests workers dags

lint-frontend: ## Lint the frontend
	cd frontend && npm run lint

typecheck: ## Type-check the frontend
	cd frontend && npm run typecheck

clean: ## Clean up containers, volumes, and images
	docker compose down -v
	docker system prune -a

health: ## Check health of all services
	@echo "Checking backend health..."
	@curl -s http://localhost:8000/health || echo "Backend not healthy"
	@echo "Checking frontend health..."
	@curl -s http://localhost:3000/api/health || echo "Frontend not healthy"
	@echo "Checking database..."
	@docker compose exec postgres pg_isready -U dataair -d dataair || echo "PostgreSQL not ready"
	@echo "Checking Redis..."
	@docker compose exec redis redis-cli ping || echo "Redis not ready"
	@echo "Checking MinIO..."
	@curl -s http://localhost:9000/minio/health/live || echo "MinIO not ready"
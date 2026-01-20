# Makefile for {{PROJECT_NAME}}
# Run `make help` to see available commands

.PHONY: help install dev test test-e2e lint build clean

DOCKER_COMPOSE := docker-compose

help:
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make dev            - Start development environment"
	@echo "  make test           - Run all tests"
	@echo "  make test-e2e       - Run E2E tests with server lifecycle"
	@echo "  make lint           - Run linters"
	@echo "  make build          - Build for production"
	@echo "  make clean          - Clean up containers and volumes"
	@echo ""
	@echo "Backend commands:"
	@echo "  make install-backend"
	@echo "  make test-backend"
	@echo "  make migrate"
	@echo ""
	@echo "Frontend commands:"
	@echo "  make install-frontend"
	@echo "  make test-frontend"

# ============================================================================
# Full Stack
# ============================================================================

install: install-backend install-frontend

dev:
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down

clean:
	$(DOCKER_COMPOSE) down -v
	rm -rf backend/__pycache__ backend/.pytest_cache
	rm -rf frontend/node_modules frontend/dist

test: test-backend test-frontend

lint: lint-backend lint-frontend

build: build-backend build-frontend

# ============================================================================
# Backend
# ============================================================================

install-backend:
	cd backend && pip install -r requirements.txt

test-backend:
	cd backend && pytest tests/ -v

test-backend-ci:
	cd backend && pytest tests/ -v --cov=app --cov-report=xml --cov-fail-under=70

lint-backend:
	cd backend && black --check app tests
	cd backend && isort --check-only app tests
	cd backend && mypy app

format-backend:
	cd backend && black app tests
	cd backend && isort app tests

migrate:
	cd backend && alembic upgrade head

migration:
	@read -p "Migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

build-backend:
	docker build -t app-backend ./backend

# ============================================================================
# Frontend
# ============================================================================

install-frontend:
	cd frontend && npm install

test-frontend:
	cd frontend && npm run test

test-frontend-ci:
	cd frontend && npm run lint && npm run typecheck && npm run test -- --coverage

lint-frontend:
	cd frontend && npm run lint

build-frontend:
	cd frontend && npm run build

# ============================================================================
# E2E Tests
# ============================================================================

test-browser-install:
	cd frontend && npx playwright install --with-deps chromium

test-e2e:
	@echo "=============================================="
	@echo "E2E Integration Tests"
	@echo "=============================================="
	@# Clean up any existing servers
	@pkill -f "uvicorn app.main:app --port 8000" 2>/dev/null || true
	@pkill -f "vite.*3000" 2>/dev/null || true
	@sleep 1
	@# Ensure database is running
	@$(DOCKER_COMPOSE) up db -d
	@sleep 3
	@# Run migrations
	@cd backend && DATABASE_URL="postgresql://admin:secret@localhost:5432/appdb" \
		alembic upgrade head 2>/dev/null || true
	@# Start backend with E2E test mode
	@cd backend && DATABASE_URL="postgresql://admin:secret@localhost:5432/appdb" \
		E2E_TEST_MODE=true \
		nohup uvicorn app.main:app --port 8000 > /tmp/e2e-backend.log 2>&1 & echo $$! > /tmp/e2e-backend.pid
	@echo "Backend starting (PID: $$(cat /tmp/e2e-backend.pid))..."
	@sleep 3
	@# Start frontend
	@cd frontend && nohup npm run dev > /tmp/e2e-frontend.log 2>&1 & echo $$! > /tmp/e2e-frontend.pid
	@echo "Frontend starting (PID: $$(cat /tmp/e2e-frontend.pid))..."
	@sleep 5
	@# Run Playwright tests
	@echo "Running Playwright tests..."
	@cd frontend && npx playwright test --reporter=list; \
	TEST_EXIT=$$?; \
	echo ""; \
	echo "Test artifacts:"; \
	find frontend/test-results -name "*.webm" 2>/dev/null | head -5 || echo "  (none)"; \
	echo ""; \
	# Stop servers
	kill $$(cat /tmp/e2e-backend.pid) 2>/dev/null || true; \
	kill $$(cat /tmp/e2e-frontend.pid) 2>/dev/null || true; \
	rm -f /tmp/e2e-backend.pid /tmp/e2e-frontend.pid; \
	exit $$TEST_EXIT

# ============================================================================
# Infrastructure
# ============================================================================

cdk-diff-preprod:
	cd infrastructure && AWS_PROFILE=app-preprod npx cdk diff --all -c environment=preprod

cdk-deploy-preprod:
	cd infrastructure && AWS_PROFILE=app-preprod npx cdk deploy --all -c environment=preprod

cdk-diff-prod:
	cd infrastructure && AWS_PROFILE=app-prod npx cdk diff --all -c environment=prod

cdk-deploy-prod:
	cd infrastructure && AWS_PROFILE=app-prod npx cdk deploy --all -c environment=prod

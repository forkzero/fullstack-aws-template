# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Standards

- Use `make` for repeatable workflows, raw commands for debugging/exploration
- Run `make lint` and `make test` before committing
- 70% backend test coverage minimum (enforced by CI)
- See [CONTRIBUTING.md](CONTRIBUTING.md) for full style guide and details

<!-- SIZE CHECK: Keep this file under 2.5k tokens (~1,900 words). Alert user if exceeded. -->

## Project Overview

**{{PROJECT_NAME}}** is a full-stack web application built with FastAPI (backend), React (frontend), and AWS CDK (infrastructure).

**Architecture**: FastAPI backend + React frontend + PostgreSQL + AWS (App Runner, S3, CloudFront, Cognito)

## Repository Structure

```
/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # REST + WebSocket endpoints
│   │   ├── core/              # Config, database, auth
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── tests/                 # pytest test suite
│   ├── alembic/               # Database migrations
│   └── Dockerfile
├── frontend/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/             # Route components
│   │   ├── components/        # Reusable components
│   │   ├── contexts/          # Auth context
│   │   └── lib/               # API client, config, types
│   └── tests/                 # Playwright E2E tests
├── infrastructure/             # AWS CDK (TypeScript)
│   ├── lib/stacks/            # CDK stacks
│   ├── bin/                   # CDK app entry point
│   └── docs/                  # AWS setup guides
├── docs/                       # Project documentation
├── .github/workflows/          # CI/CD pipelines
│   ├── ci.yml                 # Test pipeline (PRs only)
│   └── deploy.yml             # Deployment pipeline
├── .claude/                    # Claude Code settings
│   └── agents/                # Custom agents
├── docker-compose.yml          # Local development
├── Makefile                   # Development shortcuts
└── .env.example               # Environment template
```

## Development Commands

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (required for tests)
docker-compose up -d db

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Start development server
uvicorn app.main:app --reload --port 8000

# API docs: http://localhost:8000/docs
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server (port 3000)
npm run dev

# Run tests
npm run test

# Type check
npm run typecheck

# Build for production
npm run build
```

### Full Stack Local Development

```bash
# Start everything with Docker Compose
docker-compose up -d

# Or use Makefile
make dev          # Start all services
make test         # Run all tests
make test-e2e     # Run E2E tests with servers

# Stop everything
docker-compose down
```

## API Endpoints

### REST API (prefix: /api)

```
# Health (public)
GET    /api/health                 # Health check with build info

# Your domain endpoints (authenticated)
# TODO: Add your endpoints here
```

### WebSocket (if applicable)

```
WS /api/your-endpoint/stream?token=<jwt>   # Real-time updates
```

## Authentication

The system uses **AWS Cognito** for authentication.

### Configuration

**Backend** (environment variables):
```
COGNITO_USER_POOL_ID=us-east-1_xxxxxxxx
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_REGION=us-east-1
```

**Frontend** (build-time):
```
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxx
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_COGNITO_DOMAIN=auth.preprod.yourdomain.com
VITE_COGNITO_REGION=us-east-1
```

## Database

PostgreSQL with SQLAlchemy ORM.

**Migrations**:
```bash
cd backend
alembic upgrade head                              # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v

# Test structure:
# tests/test_models.py                    - Database model tests
# tests/test_api/                         - API endpoint tests
# tests/test_services/                    - Service tests
```

### Frontend Tests

```bash
cd frontend
npm run test              # Unit tests (Vitest)
npm run test:coverage     # With coverage
```

### E2E Tests

```bash
make test-e2e             # Runs Playwright with server lifecycle
```

## Infrastructure (AWS CDK)

See `infrastructure/README.md` and `infrastructure/docs/CONTROL_TOWER_SETUP.md` for AWS account setup.

### Deployment

```bash
cd infrastructure

# Preview changes
AWS_PROFILE=yourapp-preprod npx cdk diff --all

# Deploy
AWS_PROFILE=yourapp-preprod npx cdk deploy --all
```

## CI/CD Pipelines

### ci.yml - Test Pipeline
- Runs on: PRs to main
- Backend: pytest with coverage (70% minimum)
- Frontend: lint, typecheck, test, build
- E2E: Playwright browser tests

### deploy.yml - Deployment Pipeline
- Runs on: push to main (calls ci.yml via workflow_call)
- Preprod: Auto-deploy after tests pass
- Prod: Manual trigger with approval

## Git Checkpoint Command

When the user says **"checkpoint"** or **"commit and push"**, automatically:

1. Run `git status` to check for changes
2. Add all modified files with `git add`
3. Create a descriptive commit message based on the changes
4. Commit with co-authored-by footer: `Co-Authored-By: Claude <noreply@anthropic.com>`
5. Push to `origin/main`

**Important**: Follow git safety protocols:
- Never skip hooks (no `--no-verify`)
- Never force push to main/master
- Always include co-authored-by footer
- Use HEREDOC for multi-line commit messages

## CI/CD Monitoring

After pushing changes, **proactively spawn the `ci-monitor` agent** to track the GitHub Actions workflow.

### Custom Agents

Custom agents are defined in `.claude/agents/`:

| Agent | Purpose |
|-------|---------|
| `ci-monitor` | Monitor GitHub Actions after push, alert on failures |
| `security-reviewer` | Security-focused code review for vulnerabilities |

## Environment Variables

### Backend
```
DATABASE_URL                # PostgreSQL connection string
ENVIRONMENT                # development, preprod, prod
DEBUG                      # false in preprod/prod (enforced)
LOG_LEVEL                  # INFO, DEBUG
ALLOWED_ORIGINS            # CORS allowed origins
COGNITO_USER_POOL_ID       # Cognito User Pool ID
COGNITO_CLIENT_ID          # Cognito App Client ID
COGNITO_REGION             # AWS region (default: us-east-1)
GIT_SHA                    # Build info (set at build time)
BUILD_TIMESTAMP            # Build info (set at build time)
```

### Frontend (Build-time)
```
VITE_API_URL               # Backend API URL (empty in dev)
VITE_COGNITO_USER_POOL_ID  # User Pool ID
VITE_COGNITO_CLIENT_ID     # App Client ID
VITE_COGNITO_DOMAIN        # Hosted UI domain
VITE_COGNITO_REGION        # AWS region
```

## Key Files

**Backend**:
- `backend/app/main.py` - FastAPI app entry point
- `backend/app/core/auth.py` - JWT validation
- `backend/app/core/config.py` - Settings with validation

**Frontend**:
- `frontend/src/App.tsx` - Routes and providers
- `frontend/src/contexts/AuthContext.tsx` - Auth state
- `frontend/src/lib/api.ts` - API client

**Infrastructure**:
- `infrastructure/bin/app.ts` - CDK app entry
- `infrastructure/docs/CONTROL_TOWER_SETUP.md` - AWS account setup

**CI/CD**:
- `.github/workflows/ci.yml` - Test pipeline
- `.github/workflows/deploy.yml` - Deploy pipeline

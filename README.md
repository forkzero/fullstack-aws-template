# Fullstack AWS Template

A production-ready template for building full-stack web applications with:

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React + TypeScript + Vite
- **Infrastructure**: AWS CDK (App Runner, S3, CloudFront, RDS, Cognito)
- **CI/CD**: GitHub Actions with automated testing and deployment

## Quick Start

### 1. Use This Template

Click "Use this template" on GitHub to create a new repository.

### 2. Configure Your Project

Search and replace these placeholders:
- `{{PROJECT_NAME}}` → Your project name (e.g., "My App")
- `{{project-name}}` → Lowercase hyphenated (e.g., "my-app")
- `yourdomain.com` → Your domain

### 3. Local Development

```bash
# Start PostgreSQL
docker-compose up -d db

# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

### 4. Run Tests

```bash
make test           # All tests
make test-e2e       # E2E tests with server lifecycle
```

## AWS Setup

### Prerequisites

1. AWS account(s) - see [Control Tower Setup](infrastructure/docs/CONTROL_TOWER_SETUP.md)
2. Domain registered and hosted in Route 53
3. GitHub repository with Actions enabled

### Deploy Infrastructure

```bash
cd infrastructure
npm install

# Configure accounts in cdk.json
# Then deploy:
AWS_PROFILE=yourapp-preprod npx cdk deploy --all -c environment=preprod
```

### Configure GitHub Secrets

Add these secrets to your GitHub repository:

**Pre-prod:**
- `AWS_ACCESS_KEY_ID_PREPROD`
- `AWS_SECRET_ACCESS_KEY_PREPROD`
- `COGNITO_USER_POOL_ID_PREPROD`
- `COGNITO_CLIENT_ID_PREPROD`
- `COGNITO_DOMAIN_PREPROD`
- `S3_BUCKET_PREPROD`
- `CLOUDFRONT_DISTRIBUTION_ID_PREPROD`
- `ECR_REPOSITORY_PREPROD`
- `APPRUNNER_SERVICE_ARN_PREPROD`

**Production:** Same secrets with `_PROD` suffix.

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── core/           # Config, auth, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── tests/
│   └── alembic/            # Migrations
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── lib/
│   │   └── pages/
│   └── tests/
├── infrastructure/         # AWS CDK
│   ├── lib/stacks/
│   └── docs/
├── .github/workflows/      # CI/CD
├── .claude/agents/         # Claude Code agents
└── docs/
```

## CI/CD Pipeline

- **PRs**: Run tests (backend, frontend, E2E)
- **Push to main**: Run tests → Deploy to preprod
- **Manual trigger**: Deploy to production

## Features

### Backend
- JWT authentication with AWS Cognito
- Multi-tenant support (User, Organization)
- Health endpoint with build info
- Database migrations on startup
- CORS configuration
- E2E test mode for integration tests

### Frontend
- Protected routes with auth context
- API client with token handling
- Cognito OAuth integration
- Vite with hot reload
- Path aliases (`@/`)

### Infrastructure
- VPC with public/private subnets
- RDS PostgreSQL with Secrets Manager
- App Runner with VPC connector
- S3 + CloudFront for frontend
- Cognito User Pool with hosted UI
- Route 53 DNS + ACM certificates

### CI/CD
- GitHub Actions workflows
- Test coverage thresholds
- Docker layer caching
- Deployment verification
- Playwright E2E tests

### Developer Experience
- Docker Compose for local dev
- Makefile with common commands
- Claude Code agents for CI monitoring and security review

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - **Development standards, Makefile usage, code style**
- [CLAUDE.md](CLAUDE.md) - AI assistant instructions
- [Control Tower Setup](infrastructure/docs/CONTROL_TOWER_SETUP.md) - AWS account setup
- [Auth Hardening Plan](docs/AUTH_HARDENING_PLAN.md) - Security roadmap

## License

MIT

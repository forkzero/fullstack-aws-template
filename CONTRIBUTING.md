# Contributing & Development Standards

This document defines development standards, workflows, and tooling conventions.

## Development Philosophy

1. **Makefile for orchestration, raw commands for debugging**
2. **CI must pass before merge** - No exceptions
3. **Tests are not optional** - 70% coverage minimum
4. **Security is everyone's job** - Run security-reviewer agent before major PRs

---

## When to Use Makefile vs Raw Commands

### Use Makefile When:

| Scenario | Command | Why |
|----------|---------|-----|
| Starting development | `make dev` | Starts all services correctly |
| Running all tests | `make test` | Consistent with CI |
| Running E2E tests | `make test-e2e` | Handles server lifecycle |
| Before committing | `make lint` | Catches issues early |
| Deploying infrastructure | `make cdk-deploy-preprod` | Correct profile/context |

### Use Raw Commands When:

| Scenario | Command | Why |
|----------|---------|-----|
| Debugging a single test | `pytest tests/test_foo.py::test_bar -v` | More control |
| Watching frontend tests | `npm run test:watch` | Interactive mode |
| Running specific migration | `alembic upgrade +1` | Granular control |
| Checking a specific endpoint | `curl localhost:8000/api/health` | Quick inspection |
| Installing a new package | `pip install foo` | Then add to requirements.txt |

### Rule of Thumb

> **Use `make` for repeatable workflows. Use raw commands for exploration.**

---

## Code Standards

### Python (Backend)

**Style:**
- Formatter: `black` (line length 88)
- Import sorter: `isort` (black-compatible)
- Type hints: Required for public functions
- Docstrings: Required for modules, classes, public functions

**Run locally:**
```bash
make format-backend   # Auto-format
make lint-backend     # Check without fixing
```

**Example:**
```python
def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Fetch a user by their ID.

    Args:
        db: Database session
        user_id: The user's UUID

    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()
```

### TypeScript (Frontend)

**Style:**
- Formatter: Prettier (via ESLint)
- Linter: ESLint with TypeScript rules
- Strict mode: Enabled

**Run locally:**
```bash
make lint-frontend    # Check
npm run lint -- --fix # Auto-fix
```

**Conventions:**
- React components: PascalCase files (`UserProfile.tsx`)
- Utilities: camelCase files (`formatDate.ts`)
- Types: Suffix with type (`UserResponse`, `CreateUserRequest`)
- Hooks: Prefix with `use` (`useAuth`, `useApi`)

### SQL/Migrations

- Use Alembic for all schema changes
- Never modify production data in migrations
- Include both `upgrade()` and `downgrade()`
- Test migrations: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`

---

## Testing Requirements

### Coverage Thresholds

| Component | Minimum | Target |
|-----------|---------|--------|
| Backend | 70% | 85% |
| Frontend | 20% | 60% |

### Test Types

| Type | Purpose | When to Write | Command |
|------|---------|---------------|---------|
| **Unit** | Test functions in isolation | Core business logic, utilities | `make test-backend` |
| **Integration** | Test components together (API + DB) | API endpoints, service layers | `make test-backend` |
| **E2E** | Browser tests simulating users | Critical user flows | `make test-e2e` |
| **Concurrency** | Race conditions, thread safety | Shared resources, parallel ops | `pytest tests/test_concurrency.py` |
| **Antagonistic** | Behavior when dependencies fail | External APIs, DB, network | See guidance below |
| **Fuzz/Property** | Random inputs to find edge cases | Input parsing, validation | Use `hypothesis` library |
| **Load/Performance** | Response times under stress | Before production release | Use `locust` or `k6` |

### What to Test

**Always test:**
- API endpoints (happy path + error cases)
- Authentication/authorization logic
- Business logic in services
- Database queries with edge cases

**Don't test:**
- Third-party libraries
- Simple getters/setters
- Framework internals

### Antagonistic Tests (Failure Handling)

Test how your system behaves when dependencies fail. Choose the right failure strategy:

**Fail-Closed** (stop and return error) - Use for security-critical operations:
```python
def test_auth_service_down_rejects_requests():
    """When auth fails, reject all requests (fail-closed)."""
    with mock.patch('app.core.auth.verify_token', side_effect=ConnectionError):
        response = client.get("/api/protected")
        assert response.status_code == 503  # Service unavailable, not 200
```

**Fail-Open** (continue with degraded functionality) - Use for non-critical features:
```python
def test_analytics_down_continues_request():
    """When analytics fails, request still succeeds (fail-open)."""
    with mock.patch('app.services.analytics.track', side_effect=ConnectionError):
        response = client.post("/api/action")
        assert response.status_code == 200  # Action succeeds despite analytics failure
```

**When to use each:**

| Scenario | Strategy | Rationale |
|----------|----------|-----------|
| Auth/permission check fails | **Fail-closed** | Never grant access on failure |
| Payment processor fails | **Fail-closed** | Don't complete transaction |
| Rate limiter fails | **Fail-closed** | Prevent abuse |
| Analytics/tracking fails | **Fail-open** | Non-critical, don't block user |
| Recommendation engine fails | **Fail-open** | Show defaults instead |
| Cache fails | **Fail-open** | Fall back to database |
| Core feature dependency fails | **Fail-closed** | Can't provide degraded version |

**Hybrid: Circuit Breaker Pattern**
```python
# After N failures, stop trying and return cached/default response
# Periodically retry to see if service recovered
```

### Test Naming

```python
# Pattern: test_<action>_<condition>_<expected_result>
def test_create_user_with_valid_data_returns_201():
def test_create_user_with_duplicate_email_returns_409():
def test_get_user_when_not_authenticated_returns_401():
```

### Concurrency Tests

When writing tests that spawn threads (e.g., stress tests, race condition tests):

1. **Threads cannot share database sessions** - SQLAlchemy sessions are not thread-safe
2. **Threads cannot see test fixture data** - Test fixtures use transactions that are isolated from other sessions
3. **Don't import `SessionLocal` directly in threads** - It may connect to the wrong database

**Solution**: Pass a session factory configured for the test database to threads:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "postgresql://admin:secret@localhost:5432/test_db"

@pytest.fixture
def test_session_factory():
    """Session factory for threads to use."""
    engine = create_engine(TEST_DATABASE_URL)
    return sessionmaker(bind=engine)

def test_concurrent_operations(test_session_factory):
    def worker():
        session = test_session_factory()
        try:
            # Use session...
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker) for _ in range(10)]
```

---

## Git Workflow

### Branch Naming

```
feature/add-user-profile
fix/auth-token-refresh
chore/update-dependencies
```

### Commit Messages

```
<type>: <short description>

<optional body>

Co-Authored-By: Claude <noreply@anthropic.com>  # If AI-assisted
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`

### PR Requirements

Before opening a PR:
1. [ ] `make test` passes locally
2. [ ] `make lint` passes
3. [ ] New code has tests
4. [ ] CLAUDE.md updated if adding new patterns

Before merging:
1. [ ] CI passes
2. [ ] At least one approval (or self-merge if solo)
3. [ ] No unresolved comments

---

## Security Standards

### Before Major Changes

Run the security-reviewer agent:
```
Claude: "Run security review on the auth changes"
```

### Secrets Management

- **Never** commit secrets to git
- Use `.env` for local development (gitignored)
- Use AWS Secrets Manager for deployed environments
- Rotate credentials if accidentally exposed

### Authentication

- All API endpoints require authentication except `/api/health`
- Use `Depends(get_current_user)` for protected routes
- Validate token type (`access` not `id`)
- Check resource ownership before returning data

---

## Makefile Reference

```bash
make help             # Show all available commands

# Full Stack
make install          # Install all dependencies
make dev              # Start all services (docker-compose up)
make stop             # Stop all services
make clean            # Remove containers, volumes, caches
make test             # Run all tests
make lint             # Run all linters

# Backend
make install-backend  # pip install -r requirements.txt
make test-backend     # pytest tests/ -v
make lint-backend     # black --check && isort --check && mypy
make format-backend   # black && isort (auto-fix)
make migrate          # alembic upgrade head
make migration        # Create new migration (prompts for message)

# Frontend
make install-frontend # npm install
make test-frontend    # npm run test
make lint-frontend    # npm run lint

# E2E
make test-e2e         # Full E2E with server lifecycle
make test-browser-install  # Install Playwright browsers

# Infrastructure
make cdk-diff-preprod    # Preview CDK changes
make cdk-deploy-preprod  # Deploy to preprod
make cdk-diff-prod       # Preview prod changes
make cdk-deploy-prod     # Deploy to production
```

---

## CI/CD Pipeline

### What Runs When

| Event | Workflow | Jobs |
|-------|----------|------|
| PR to main | `ci.yml` | backend tests, frontend tests, playwright |
| Push to main | `deploy.yml` | tests (via ci.yml) → deploy preprod |
| Manual trigger | `deploy.yml` | tests → deploy preprod OR prod |

### If CI Fails

1. Check the failed job in GitHub Actions
2. Run the same command locally:
   - Backend: `make test-backend-ci`
   - Frontend: `make test-frontend-ci`
   - E2E: `make test-e2e`
3. Fix and push

### Deployment Verification

After deploy, the pipeline verifies the correct version is running by checking `/api/health` for the expected `git_sha`.

---

## Adding New Features

### Checklist

1. **Plan**: Update CLAUDE.md if adding new patterns
2. **Implement**: Follow code standards above
3. **Test**: Add tests, ensure coverage
4. **Document**: Update README if user-facing
5. **Review**: Run `make lint`, `make test`
6. **Security**: Run security-reviewer for auth/data changes
7. **Deploy**: PR → merge → auto-deploy to preprod

### Adding a New API Endpoint

```bash
# 1. Create the route
# backend/app/api/widgets.py

# 2. Create schemas
# backend/app/schemas/widget.py

# 3. Add to main.py
# app.include_router(widgets.router, ...)

# 4. Write tests
# backend/tests/test_api/test_widgets.py

# 5. Run tests
make test-backend
```

### Adding a New Frontend Page

```bash
# 1. Create the page
# frontend/src/pages/WidgetsPage.tsx

# 2. Add route in App.tsx

# 3. Write tests (optional for pages, required for components)

# 4. Run tests
make test-frontend
```

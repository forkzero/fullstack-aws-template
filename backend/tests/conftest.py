"""Pytest fixtures for backend tests."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models import User

# Test database URL
TEST_DATABASE_URL = "postgresql://admin:secret@localhost:5432/test_appdb"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    return create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        cognito_sub="test-user-sub",
        email="test@example.com",
        display_name="Test User",
        role="member"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

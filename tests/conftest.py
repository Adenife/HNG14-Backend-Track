"""
Test configuration and shared fixtures.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Point to test database
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "testuser")
os.environ.setdefault("POSTGRES_PASSWORD", "testpassword")
os.environ.setdefault("POSTGRES_DB", "testdb")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_HOSTNAME", "localhost")
os.environ.setdefault("GITHUB_CLIENT_ID", "fake-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "fake-client-secret")
os.environ.setdefault("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "3")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_MINUTES", "5")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

from main import app  # noqa: E402
from app.core.database import get_db, Base  # noqa: E402
from app.models import models  # noqa: F401, E402  — registers all ORM models

TEST_DB_URL = (
    f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ['POSTGRES_HOSTNAME']}:{os.environ['DATABASE_PORT']}"
    f"/{os.environ['POSTGRES_DB']}"
)

engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    """Yield a transactional test session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI test client with DB session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(db_session):
    """Create an admin user and return a valid access token."""
    from app.models.models import User
    from app.core.security import create_access_token
    from uuid6 import uuid7

    user = User(
        id=uuid7(),
        github_id="admin-github-id",
        username="adminuser",
        email="admin@test.com",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": "admin"})
    return token, user


@pytest.fixture
def analyst_token(db_session):
    """Create an analyst user and return a valid access token."""
    from app.models.models import User
    from app.core.security import create_access_token
    from uuid6 import uuid7

    user = User(
        id=uuid7(),
        github_id="analyst-github-id",
        username="analystuser",
        email="analyst@test.com",
        role="analyst",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": "analyst"})
    return token, user

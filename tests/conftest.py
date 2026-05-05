import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models import models
import uuid
import datetime

# Use an in-memory SQLite for testing if possible, 
# but keep in mind Postgres-specific types might fail.
# For this task, we will mock the DB session to be safe.

@pytest.fixture
def mock_db(mocker):
    return mocker.Mock()

@pytest.fixture
def client(mocker):
    # Mock database
    mock_session = mocker.Mock()
    app.dependency_overrides[get_db] = lambda: mock_session

    # Mock authentication
    mock_user = models.User(
        id=uuid.uuid4(),
        github_id="12345",
        username="testuser",
        email="test@example.com",
        role="admin",
        is_active=True,
        created_at=datetime.datetime.now(datetime.UTC)
    )
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[require_admin] = lambda: mock_user
    
    with TestClient(app) as c:
        c.headers.update({"X-API-Version": "1"})
        yield c
    
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user():
    return models.User(
        id=uuid.uuid4(),
        github_id="admin123",
        username="admin",
        role="admin"
    )

@pytest.fixture
def analyst_user():
    return models.User(
        id=uuid.uuid4(),
        github_id="analyst123",
        username="analyst",
        role="analyst"
    )

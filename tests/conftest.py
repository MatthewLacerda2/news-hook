import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.main import app
from fastapi.testclient import TestClient
from unittest.mock import patch

# Create a test database URL for SQLite in-memory database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# Create the test engine
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def test_db():
    """SQLite in-memory test database fixture"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create a test database session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        # Clean up after test
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture
def mock_google_verify():
    """Fixture to mock Google token verification"""
    with patch('app.api.v1.endpoints.auth.verify_google_token') as mock:
        # This simulates what we get back from Google's verification
        mock.return_value = {
            'email': 'test@example.com',
            'sub': '12345',  # This is Google's user ID
            'name': 'Test User'
        }
        yield mock

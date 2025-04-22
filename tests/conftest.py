import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from uuid import UUID

# Set test environment variables before importing app
os.environ["GOOGLE_CLIENT_ID"] = "dummy_client_id"
os.environ["GOOGLE_CLIENT_SECRET"] = "dummy_client_secret"
os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8000/auth/callback"

from app.models.base import Base
from app.main import app
from fastapi.testclient import TestClient
from app.models.llm_models import LLMModel

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

@pytest.fixture
def sample_llm_models(test_db):
    models = [
        LLMModel(
            id=UUID("550e8400-e29b-41d4-a716-446655440001"),
            model_name="gemini-2.5-pro",
            input_token_price=0.001,
            output_token_price=0.002,
            is_active=True
        ),
        LLMModel(
            id=UUID("550e8400-e29b-41d4-a716-446655440002"),
            model_name="llama3.1",
            input_token_price=0.003,
            output_token_price=0.004,
            is_active=False
        ),
        LLMModel(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            model_name="gpt-4o",
            input_token_price=0.0015,
            output_token_price=0.0030,
            is_active=True
        )
    ]
    
    for model in models:
        test_db.add(model)
    test_db.commit()
    
    return models

import os

# Set test environment variables BEFORE importing anything
os.environ["GOOGLE_CLIENT_ID"] = "dummy_client_id"
os.environ["GOOGLE_CLIENT_SECRET"] = "dummy_client_secret"
os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8000/auth/callback"
os.environ["SECRET_KEY"] = "your-secret-key-here"  # Match the key from app/core/config.py

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import uuid
import app.models
from httpx import AsyncClient
from app.models.base import Base
from app.models.llm_models import LLMModel
from app.main import app
from app.core.database import get_db
from httpx import ASGITransport
from app.models.agent_controller import AgentController
from sqlalchemy.sql import text

# Create a test database URL for SQLite in-memory database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create the test engine
test_engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create test session factory
TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Override the database dependency
async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest_asyncio.fixture
async def test_db():
    """SQLite in-memory test database fixture"""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a test database session
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            # Clean up after test
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    """Async test client fixture"""
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    # Clean up the override after the test
    app.dependency_overrides.clear()

@pytest.fixture
def mock_google_verify():
    """Fixture to mock Google token verification"""
    from google.oauth2 import id_token
    
    def mock_verify_oauth2_token(token, request, client_id):
        if token != "valid_google_token":
            raise ValueError("Invalid token")
        return {
            "iss": "accounts.google.com",
            "sub": "12345",  # Google's unique user ID
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "aud": client_id  # This should match settings.GOOGLE_CLIENT_ID
        }

    # Mock the Google verification function instead
    with patch('google.oauth2.id_token.verify_oauth2_token', side_effect=mock_verify_oauth2_token) as mock:
        yield mock

@pytest_asyncio.fixture
async def sample_llm_models(test_db):
    models = [
        LLMModel(
            id=str(uuid.uuid4()),
            model_name="gemini-2.5-pro",
            input_token_price=0.001,
            output_token_price=0.002,
            is_active=True
        ),
        LLMModel(
            id=str(uuid.uuid4()),
            model_name="llama3.1",
            input_token_price=0.003,
            output_token_price=0.004,
            is_active=False
        ),
        LLMModel(
            id=str(uuid.uuid4()),
            model_name="gpt-4o",
            input_token_price=0.0015,
            output_token_price=0.0030,
            is_active=True
        )
    ]
    
    for model in models:
        test_db.add(model)
    await test_db.commit()
    
    return models

@pytest_asyncio.fixture
async def verify_tables(test_db):
    """Verify that all required tables are created"""
    async with test_engine.connect() as conn:
        # This will show all tables that exist in the database
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = result.fetchall()
        print("Created tables:", [table[0] for table in tables])

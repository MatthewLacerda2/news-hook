import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import app.models
from httpx import AsyncClient
from app.models.base import Base
from app.models.llm_models import LLMModel
from app.main import app
from app.core.database import get_db
from httpx import ASGITransport
from app.models.agent_controller import AgentController
from sqlalchemy.sql import text
from app.utils.llm_response_formats import LLMValidationFormat

SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

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
        if token == "valid_google_token" or token == "valid_google_token_1":
            return {
                "iss": "accounts.google.com",
                "sub": "12345",
                "email": "test1@example.com",
                "email_verified": True,
                "name": "Test User 1",
                "aud": client_id
            }
        elif token == "valid_google_token_2":
            return {
                "iss": "accounts.google.com",
                "sub": "67890",
                "email": "test2@example.com",
                "email_verified": True,
                "name": "Test User 2",
                "aud": client_id
            }
        raise ValueError("Invalid token")

    with patch('google.oauth2.id_token.verify_oauth2_token', side_effect=mock_verify_oauth2_token) as mock:
        yield mock

@pytest_asyncio.fixture
async def sample_llm_models(test_db):
    models = [
        LLMModel(
            model_name="gemini-2.0-flash",
            input_token_price=0.001,
            output_token_price=0.002,
            is_active=True
        ),
        LLMModel(
            model_name="gemini-2.5-flash",
            input_token_price=0.003,
            output_token_price=0.004,
            is_active=True
        ),
        LLMModel(
            model_name="gemini-2.5-pro",
            input_token_price=0.0015,
            output_token_price=0.0030,
            is_active=False
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

@pytest_asyncio.fixture
async def valid_user_with_credits(test_db, client, mock_google_verify):
    mock_google_verify.return_value = {
        'email': 'test@example.com',
        'sub': '12345',
        'name': 'Test User'
    }
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]

    user = await test_db.get(AgentController, user_data["id"])
    user.credit_balance = 10
    await test_db.commit()
    await test_db.refresh(user)

    return user_data

@pytest.fixture
def mock_llm_validation():
    """Fixture to mock LLM validation responses"""
    
    async def mock_get_llm_validation(*args, **kwargs):
        return LLMValidationFormat(
            approval=True,
            chance_score=0.95,
            reason="This is a valid alert request",
            keywords=["bitcoin", "price", "50000"]
        )

    with patch('app.api.v1.endpoints.alert.get_llm_validation', side_effect=mock_get_llm_validation) as mock:
        yield mock
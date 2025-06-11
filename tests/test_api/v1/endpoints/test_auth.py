import pytest
from app.schemas.agent_controller import TokenResponse
import uuid
from datetime import timedelta
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_signup_successful(client, mock_google_verify, test_db):
    """Test successful signup with valid Google token"""
    response = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 201
    token_response = TokenResponse.model_validate(response.json())
    
    assert token_response.token_type == "bearer"
    assert token_response.agent_controller.email == "test1@example.com"
    assert token_response.agent_controller.name == "Test User 1"
    assert token_response.agent_controller.google_id == "12345"
    assert token_response.agent_controller.credit_balance == 10
    assert token_response.agent_controller.api_key is not None

@pytest.mark.asyncio
async def test_signup_invalid_token(client, mock_google_verify):
    """Test signup with invalid Google token"""
    mock_google_verify.side_effect = Exception("Invalid token")
    
    response = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token"

@pytest.mark.asyncio
async def test_signup_existing_user(client, mock_google_verify, test_db):
    """Test signup attempt with existing Google account"""
    first_response = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    second_response = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "User already exists"

@pytest.mark.asyncio
async def test_signup_missing_token(client):
    """Test signup without providing token"""
    response = await client.post(
        "/api/v1/auth/signup",
        json={}
    )
    
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_login_successful(client, mock_google_verify, test_db):
    """Test successful login with valid Google token for existing user"""
    
    await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )    
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 200
    token_response = TokenResponse.model_validate(response.json())
    
    assert token_response.token_type == "bearer"
    assert token_response.agent_controller.email == "test1@example.com"
    assert token_response.agent_controller.name == "Test User 1"
    assert token_response.agent_controller.google_id == "12345"
    assert token_response.agent_controller.credit_balance == 10
    assert token_response.agent_controller.api_key is not None

@pytest.mark.asyncio
async def test_login_nonexistent_user(client, mock_google_verify, test_db):
    """Test login attempt with Google account that hasn't signed up"""
    
    mock_google_verify.return_value = {
        'email': 'nonexistent@example.com',
        'sub': 'nonexistent_google_id',
        'name': 'Nonexistent User'
    }
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_login_invalid_token(client, mock_google_verify):
    """Test login with invalid Google token"""
    mock_google_verify.side_effect = Exception("Invalid token")
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"access_token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token"

@pytest.mark.asyncio
async def test_login_missing_token(client):
    """Test login without providing token"""
    response = await client.post(
        "/api/v1/auth/login",
        json={}
    )
    
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_check_credits_successful(client, mock_google_verify, test_db):
    """Test successful credits check for authenticated user"""
    
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    access_token = signup_response.json()["access_token"]
    
    response = await client.get(
        "/api/v1/auth/credits",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "credit_balance" in data
    assert isinstance(data["credit_balance"], float)

@pytest.mark.asyncio
async def test_check_credits_unauthorized(client):
    """Test credits check without authentication"""
    response = await client.get("/api/v1/auth/credits")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_check_credits_invalid_token(client):
    """Test credits check with invalid token"""
    response = await client.get(
        "/api/v1/auth/credits",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

@pytest.mark.asyncio
async def test_check_credits_user_not_found(client, verify_tables):
    """Test credits check for non-existent user"""
    
    nonexistent_user_id = str(uuid.uuid4())
    access_token = create_access_token(
        data={"sub": nonexistent_user_id},
        expires_delta=timedelta(minutes=15)
    )
    
    response = await client.get(
        "/api/v1/auth/credits",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_delete_account_successful(client, mock_google_verify, test_db):
    """Test successful account deletion with valid token"""
    
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    access_token = signup_response.json()["access_token"]
    
    test_prompts = [
        {
            "prompt": "Test prompt 1",
            "http_method": "GET",
            "http_url": "http://test1.com"
        },
        {
            "prompt": "Test prompt 2",
            "http_method": "POST",
            "http_url": "http://test2.com"
        }
    ]
    
    for prompt in test_prompts:
        await client.post(
            "/api/v1/alerts/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=prompt
        )
    
    response = await client.delete(
        "/api/v1/auth/account",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Account successfully deleted"
    
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"access_token": "valid_google_token"}
    )
    assert login_response.status_code == 404
    
    alerts_response = await client.get(
        "/api/v1/alerts/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert alerts_response.status_code == 403

@pytest.mark.asyncio
async def test_delete_account_invalid_token(client):
    """Test account deletion with invalid token"""
    response = await client.delete(
        "/api/v1/auth/account",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
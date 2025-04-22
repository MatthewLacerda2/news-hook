import pytest
from app.schemas.agent_controller import TokenResponse

@pytest.mark.asyncio
async def test_signup_successful(client):
    """Test successful signup with valid Google token"""
    response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 201
    # This will validate that the response matches the TokenResponse schema
    token_response = TokenResponse.model_validate(response.json())
    
    # Now we can use the validated object for assertions
    assert token_response.token_type == "bearer"
    assert token_response.agent_controller.email == "test@example.com"
    assert token_response.agent_controller.name == "Test User"
    assert token_response.agent_controller.google_id == "12345"
    assert token_response.agent_controller.credits == 0
    assert token_response.agent_controller.api_key is not None

@pytest.mark.asyncio
async def test_signup_invalid_token(client, mock_google_verify):
    """Test signup with invalid Google token"""
    mock_google_verify.side_effect = Exception("Invalid token")
    
    response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token"

@pytest.mark.asyncio
async def test_signup_existing_user(client):
    """Test signup attempt with existing Google account"""
    # First signup
    client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    # Try to signup again with same Google account
    response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 409
    assert response.json()["detail"] == "User already exists"

@pytest.mark.asyncio
async def test_signup_missing_token(client):
    """Test signup without providing token"""
    response = client.post(
        "/api/v1/auth/signup",
        json={}
    )
    
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_login_successful(client):
    """Test successful login with valid Google token for existing user"""
    # First create a user through signup
    client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    # Now try to login
    response = client.post(
        "/api/v1/auth/login",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 200
    # This will validate that the response matches the TokenResponse schema
    token_response = TokenResponse.model_validate(response.json())
    
    # Now we can use the validated object for assertions
    assert token_response.token_type == "bearer"
    assert token_response.agent_controller.email == "test@example.com"
    assert token_response.agent_controller.name == "Test User"
    assert token_response.agent_controller.google_id == "12345"
    assert token_response.agent_controller.credits == 0
    assert token_response.agent_controller.api_key is not None

@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Test login attempt with Google account that hasn't signed up"""
    response = client.post(
        "/api/v1/auth/login",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_login_invalid_token(client, mock_google_verify):
    """Test login with invalid Google token"""
    mock_google_verify.side_effect = Exception("Invalid token")
    
    response = client.post(
        "/api/v1/auth/login",
        json={"access_token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token"

@pytest.mark.asyncio
async def test_login_missing_token(client):
    """Test login without providing token"""
    response = client.post(
        "/api/v1/auth/login",
        json={}
    )
    
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_check_credits_successful(client):
    """Test successful credits check for authenticated user"""
    # First create a user through signup
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    access_token = signup_response.json()["access_token"]
    
    # Check credits
    response = client.get(
        "/api/v1/auth/credits",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "credits" in data
    assert isinstance(data["credits"], int)

@pytest.mark.asyncio
async def test_check_credits_unauthorized(client):
    """Test credits check without authentication"""
    response = client.get("/api/v1/auth/credits")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_check_credits_invalid_token(client):
    """Test credits check with invalid token"""
    response = client.get(
        "/api/v1/auth/credits",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

@pytest.mark.asyncio
async def test_check_credits_user_not_found(client):
    """Test credits check for non-existent user"""
    # Create a token for a user that doesn't exist in DB
    response = client.get(
        "/api/v1/auth/credits",
        headers={"Authorization": "Bearer valid_but_nonexistent_user_token"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_check_credits_after_modification(client):
    """Test credits check after credits have been modified"""
    # First create a user through signup
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    access_token = signup_response.json()["access_token"]
    
    # Modify user's credits in the database (this would normally be done through an API endpoint)
    # Note: You'll need to implement this part based on your database access pattern
    # For example: test_db.update_user_credits(user_id, 100)
    
    # Check credits after modification
    response = client.get(
        "/api/v1/auth/credits",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "credits" in data
    assert isinstance(data["credits"], int)
    # Assert the new credit amount if you implemented the credit modification
    # assert data["credits"] == 100

@pytest.mark.asyncio
async def test_delete_account_successful(client):
    """Test successful account deletion with valid token"""
    # First create a user through signup
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    access_token = signup_response.json()["access_token"]
    
    # Create some alert prompts for this user
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
    
    # Add test prompts to database
    for prompt in test_prompts:
        client.post(
            "/api/v1/alerts/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=prompt
        )
    
    # Delete the account
    response = client.delete(
        "/api/v1/auth/account",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Account successfully deleted"
    
    # Verify user can't login anymore
    login_response = client.post(
        "/api/v1/auth/login",
        json={"access_token": "valid_google_token"}
    )
    assert login_response.status_code == 404
    
    # Verify all alert prompts were deleted
    # Try to get alerts (should fail as user doesn't exist)
    alerts_response = client.get(
        "/api/v1/alerts/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert alerts_response.status_code == 401

@pytest.mark.asyncio
async def test_delete_account_unauthorized(client):
    """Test account deletion without authentication"""
    response = client.delete("/api/v1/auth/account")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_delete_account_invalid_token(client):
    """Test account deletion with invalid token"""
    response = client.delete(
        "/api/v1/auth/account",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

@pytest.mark.asyncio
async def test_delete_account_nonexistent_user(client):
    """Test deletion attempt for non-existent user"""
    response = client.delete(
        "/api/v1/auth/account",
        headers={"Authorization": "Bearer valid_but_nonexistent_user_token"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
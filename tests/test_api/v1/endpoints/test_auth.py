import pytest

def test_signup_successful(client, mock_google_verify, test_db):
    """Test successful signup with valid Google token"""
    response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Check response structure
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    
    # Check user data
    assert "agent_controller" in data
    user = data["agent_controller"]
    assert user["email"] == "test@example.com"
    assert user["name"] == "Test User"
    assert user["google_id"] == "12345"
    assert "api_key" in user
    assert user["credits"] == 0

def test_signup_invalid_token(client, mock_google_verify):
    """Test signup with invalid Google token"""
    mock_google_verify.side_effect = Exception("Invalid token")
    
    response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token"

def test_signup_existing_user(client, mock_google_verify, test_db):
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

def test_signup_missing_token(client):
    """Test signup without providing token"""
    response = client.post(
        "/api/v1/auth/signup",
        json={}
    )
    
    assert response.status_code == 422  # Validation error

def test_login_successful(client, mock_google_verify, test_db):
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
    
    assert response.status_code == 200  # 200 for login vs 201 for signup
    data = response.json()
    
    # Check response structure
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    
    # Check user data
    assert "agent_controller" in data
    user = data["agent_controller"]
    assert user["email"] == "test@example.com"
    assert user["name"] == "Test User"
    assert user["google_id"] == "12345"
    assert "api_key" in user
    assert user["credits"] == 0

def test_login_nonexistent_user(client, mock_google_verify, test_db):
    """Test login attempt with Google account that hasn't signed up"""
    response = client.post(
        "/api/v1/auth/login",
        json={"access_token": "valid_google_token"}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_login_invalid_token(client, mock_google_verify):
    """Test login with invalid Google token"""
    mock_google_verify.side_effect = Exception("Invalid token")
    
    response = client.post(
        "/api/v1/auth/login",
        json={"access_token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token"

def test_login_missing_token(client):
    """Test login without providing token"""
    response = client.post(
        "/api/v1/auth/login",
        json={}
    )
    
    assert response.status_code == 422  # Validation error

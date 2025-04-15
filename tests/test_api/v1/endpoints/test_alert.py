import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from app.schemas.alert_prompt import AlertPromptCreateRequestBase, HttpMethod

def test_create_alert_successful(client, test_db):
    """Test successful alert creation with valid data"""
    # First create a user and get their token (similar to auth tests)
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/crypto-alert",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 51000, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "prompt" in data
    assert "understood_intent" in data
    assert "created_at" in data

def test_create_alert_invalid_api_key(client, test_db):
    """Test alert creation with invalid API key"""
    alert_data = {
        "api_key": "invalid_api_key",
        "user_id": str(uuid4()),
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test"
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

def test_create_alert_mismatched_user_api_key(client, test_db):
    """Test alert creation with API key not owned by user"""
    # Create first user
    signup1 = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token_1"}
    )
    user1_data = signup1.json()["agent_controller"]
    
    # Create second user
    mock_google_verify.return_value = {
        'email': 'test2@example.com',
        'sub': '67890',
        'name': 'Test User 2'
    }
    signup2 = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token_2"}
    )
    user2_data = signup2.json()["agent_controller"]
    
    # Try to create alert with user1's API key but user2's ID
    alert_data = {
        "api_key": user1_data["api_key"],
        "user_id": user2_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test"
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "API key does not match user" in response.json()["detail"]

def test_create_alert_insufficient_credits(client, test_db):
    """Test alert creation with insufficient credits"""
    # Create user with 0 credits
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test"
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 401
    assert "Insufficient credits" in response.json()["detail"]

def test_create_alert_invalid_url(client, test_db):
    """Test alert creation with invalid URL"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "not-a-valid-url"
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]

def test_create_alert_invalid_parsed_intent(client, test_db):
    """Test alert creation with invalid parsed_intent JSON"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "parsed_intent": "not-a-valid-json"
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "Invalid parsed_intent format" in response.json()["detail"]

def test_create_alert_invalid_example_response(client, test_db):
    """Test alert creation with invalid example_response JSON"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "example_response": "not-a-valid-json"
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "Invalid example_response format" in response.json()["detail"]

def test_create_alert_invalid_max_datetime(client, test_db):
    """Test alert creation with invalid max_datetime values"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    # Test with datetime too soon
    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "max_datetime": (datetime.now() + timedelta(minutes=20)).isoformat()
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "max_datetime must be at least 30 minutes in the future" in response.json()["detail"]
    
    # Test with datetime too far in future
    alert_data["max_datetime"] = (datetime.now() + timedelta(days=400)).isoformat()
    response = client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "max_datetime cannot be more than 1 year in the future" in response.json()["detail"]
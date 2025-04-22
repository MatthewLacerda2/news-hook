from datetime import datetime, timedelta
from uuid import uuid4
from app.schemas.alert_prompt import AlertPromptCreateSuccessResponse, AlertPromptListResponse, AlertPromptItem
from app.models.alert_prompt import AlertStatus

def test_create_alert_successful(client):
    """Test successful alert creation with valid data"""
    # First create a user and get their token (similar to auth tests)
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    alert_data = {
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/crypto-alert",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 50001, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=300)).isoformat(),
        "llm_model": "gemini-2.5-pro"
    }
    
    response = client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": user_data["api_key"]},  # API key in header
        json=alert_data
    )
    
    assert response.status_code == 201
    # This will raise a validation error if the response doesn't match the schema
    AlertPromptCreateSuccessResponse.model_validate(response.json())

def test_create_alert_invalid_api_key(client):
    """Test alert creation with invalid API key"""
    alert_data = {
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test"
    }
    
    response = client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": "invalid_api_key"},  # Invalid API key in header
        json=alert_data
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

def test_create_alert_mismatched_user_api_key(client, mock_google_verify):
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

def test_create_alert_insufficient_credits(client):
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

def test_create_alert_invalid_url(client):
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

def test_create_alert_invalid_parsed_intent(client):
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

def test_create_alert_invalid_example_response(client):
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

def test_create_alert_invalid_max_datetime(client):
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

def test_create_alert_invalid_llm_model(client):
    """Test alert creation with invalid LLM model"""
    # First create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    alert_data = {
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "llm_model": "nonexistent_model_name"
    }
    
    response = client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": user_data["api_key"]},
        json=alert_data
    )
    
    assert response.status_code == 400
    assert "Invalid LLM model" in response.json()["detail"]

def test_list_alerts_successful(client):
    """Test successful alert listing with valid parameters"""
    # First create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    # Valid request with all optional parameters
    list_params = {
        "offset": 0,
        "limit": 50,
        "prompt_contains": "bitcoin",
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat(),
        "created_after": datetime.now().isoformat()
    }
    
    response = client.get(
        "/api/v1/alerts/",
        params=list_params,
        headers={"X-API-Key": user_data["api_key"]}
    )
    assert response.status_code == 200
    
    # Validate response matches AlertPromptListResponse schema
    data = response.json()
    AlertPromptListResponse.model_validate(data)

def test_list_alerts_invalid_parameters(client):
    """Test alert listing with invalid parameter types"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    api_key = user_data["api_key"]
    
    # Test invalid offset/limit
    invalid_pagination_params = {
        "offset": -1,
        "limit": 101
    }
    response = client.get(
        "/api/v1/alerts/",
        params=invalid_pagination_params,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 400
    assert "Invalid pagination parameters" in response.json()["detail"]
    
    # Test invalid datetime format
    invalid_datetime_params = {
        "created_after": "not-a-datetime"
    }
    response = client.get(
        "/api/v1/alerts/",
        params=invalid_datetime_params,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 400
    assert "Invalid datetime format" in response.json()["detail"]

def test_list_alerts_datetime_validation(client):
    """Test datetime validation between created_after and max_datetime"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    now = datetime.now()
    params = {
        "created_after": (now + timedelta(days=2)).isoformat(),
        "max_datetime": (now + timedelta(days=1)).isoformat()
    }
    
    response = client.get(
        "/api/v1/alerts/",
        params=params,
        headers={"X-API-Key": user_data["api_key"]}
    )
    assert response.status_code == 400
    assert "created_after cannot be later than max_datetime" in response.json()["detail"]

def test_list_alerts_minimal_parameters(client):
    """Test alert listing with no parameters (just authentication)"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    response = client.get(
        "/api/v1/alerts/",
        headers={"X-API-Key": user_data["api_key"]}
    )
    assert response.status_code == 200
    
    # Validate response
    data = response.json()
    AlertPromptListResponse.model_validate(data)

def test_list_alerts_invalid_api_key(client):
    """Test alert listing with invalid API key"""
    response = client.get(
        "/api/v1/alerts/",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

def test_get_alert_successful(client):
    """Test successful alert retrieval"""
    # First create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    api_key = user_data["api_key"]
    
    # Create an alert first
    alert_data = {
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/crypto-alert",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 50001, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    create_response = client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key},
        json=alert_data
    )
    assert create_response.status_code == 201
    alert_id = create_response.json()["id"]
    
    # Get the specific alert
    response = client.get(
        f"/api/v1/alerts/{alert_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    alert = response.json()
    
    # Validate the response matches our schema
    AlertPromptItem.model_validate(alert)
    
    # Verify the alert data matches what we created
    assert alert["prompt"] == alert_data["prompt"]
    assert alert["http_method"] == alert_data["http_method"]
    assert alert["http_url"] == alert_data["http_url"]

def test_get_alert_not_found(client):
    """Test attempting to get a non-existent alert"""
    # First create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    api_key = user_data["api_key"]
    
    # Try to get a non-existent alert using a random UUID
    non_existent_id = str(uuid4())
    response = client.get(
        f"/api/v1/alerts/{non_existent_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

def test_cancel_alert_successful(client):
    """Test successful alert cancellation"""
    # First create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    api_key = user_data["api_key"]
    
    # Create an alert first
    alert_data = {
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/crypto-alert",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 50001, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    create_response = client.post(
        "/api/v1/alerts/", 
        headers={"X-API-Key": api_key},
        json=alert_data
    )
    assert create_response.status_code == 201
    alert_id = create_response.json()["id"]
    
    # Now cancel the alert using PATCH
    response = client.patch(
        f"/api/v1/alerts/{alert_id}/cancel",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    
    # Verify the alert is now cancelled by getting it
    list_response = client.get(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key}
    )
    assert list_response.status_code == 200
    alerts = list_response.json()["alerts"]
    cancelled_alert = next(alert for alert in alerts if alert["id"] == alert_id)
    assert cancelled_alert["status"] == AlertStatus.CANCELLED

def test_cancel_alert_invalid_api_key(client):
    """Test attempting to cancel an alert with invalid API key"""
    response = client.patch(
        f"/api/v1/alerts/{str(uuid4())}/cancel",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 403
    assert "Unauthorized" in response.json()["detail"]

def test_cancel_alert_wrong_user(client, mock_google_verify):
    """Test attempting to cancel an alert belonging to another user"""
    # Create first user and their alert
    signup1 = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token_1"}
    )
    user1_data = signup1.json()["agent_controller"]
    api_key1 = user1_data["api_key"]
    
    alert_data = {
        "prompt": "Test alert",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    create_response = client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key1},
        json=alert_data
    )
    assert create_response.status_code == 201
    alert_id = create_response.json()["id"]
    
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
    api_key2 = user2_data["api_key"]
    
    # Try to cancel first user's alert with second user's API key
    response = client.patch(
        f"/api/v1/alerts/{alert_id}/cancel",
        headers={"X-API-Key": api_key2}
    )
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

def test_cancel_nonexistent_alert(client):
    """Test attempting to cancel an alert that doesn't exist"""
    # Create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    api_key = user_data["api_key"]
    
    response = client.patch(
        f"/api/v1/alerts/{str(uuid4())}/cancel",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]
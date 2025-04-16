from datetime import datetime, timedelta
from uuid import uuid4
from app.schemas.alert_prompt import AlertPromptPriceCheckSuccessResponse, AlertPromptCreateSuccessResponse, AlertMode, AlertPromptListResponse

def test_create_alert_successful(client):
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
        "example_response": {"price": 50001, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=300)).isoformat()
    }
    
    response = client.post("/api/v1/alerts/", json=alert_data)
    
    assert response.status_code == 201
    # This will raise a validation error if the response doesn't match the schema
    AlertPromptCreateSuccessResponse.model_validate(response.json())

def test_create_alert_invalid_api_key(client):
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

def test_check_alert_price_successful(client):
    """Test successful alert price check with valid data"""
    price_check_data = {
        "mode": AlertMode.pro.value,
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 50001, "alert": True}
    }
    
    response = client.post("/api/v1/alerts/price-check", json=price_check_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] in AlertMode._value2member_map_
    AlertPromptPriceCheckSuccessResponse.model_validate(data)

def test_check_alert_price_short_prompt(client):
    """Test alert price check with prompt shorter than 8 characters"""
    price_check_data = {
        "mode": AlertMode.base.value,
        "prompt": "short",
        "parsed_intent": {"test": "data"},
        "example_response": {"test": "data"}
    }
    
    response = client.post("/api/v1/alerts/price-check", json=price_check_data)
    assert response.status_code == 400
    assert "Prompt must be at least 8 characters long" in response.json()["detail"]

def test_check_alert_price_invalid_parsed_intent(client):
    """Test alert price check with invalid parsed_intent JSON"""
    price_check_data = {
        "mode": "CONTINUOUS",
        "prompt": "Monitor Bitcoin price changes",
        "parsed_intent": "not-a-valid-json",
        "example_response": {"test": "data"}
    }
    
    response = client.post("/api/v1/alerts/price-check", json=price_check_data)
    assert response.status_code == 400
    assert "Invalid parsed_intent format" in response.json()["detail"]

def test_check_alert_price_invalid_example_response(client):
    """Test alert price check with invalid example_response JSON"""
    price_check_data = {
        "mode": "CONTINUOUS",
        "prompt": "Monitor Bitcoin price changes",
        "parsed_intent": {"test": "data"},
        "example_response": "not-a-valid-json"
    }
    
    response = client.post("/api/v1/alerts/price-check", json=price_check_data)
    assert response.status_code == 400
    assert "Invalid example_response format" in response.json()["detail"]

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
        "user_id": user_data["id"],
        "tags": ["crypto", "bitcoin"],
        "offset": 0,
        "limit": 50,
        "prompt_contains": "bitcoin",
        "http_method": "POST",
        "base_url": "https://webhook.example.com",
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat(),
        "created_at": datetime.now().isoformat(),
        "status": "ACTIVE"
    }
    
    response = client.get("/api/v1/alerts/", params=list_params)
    assert response.status_code == 200
    
    # Validate response matches AlertPromptListResponse schema
    data = response.json()
    AlertPromptListResponse.model_validate(data)

def test_list_alerts_invalid_enum_values(client):
    """Test alert listing with invalid enum values"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    # Test invalid HTTP method
    invalid_method_params = {
        "user_id": user_data["id"],
        "http_method": "INVALID_METHOD"
    }
    response = client.get("/api/v1/alerts/", params=invalid_method_params)
    assert response.status_code == 400
    assert "Invalid http_method value" in response.json()["detail"]
    
    # Test invalid status
    invalid_status_params = {
        "user_id": user_data["id"],
        "status": "INVALID_STATUS"
    }
    response = client.get("/api/v1/alerts/", params=invalid_status_params)
    assert response.status_code == 400
    assert "Invalid status value" in response.json()["detail"]

def test_list_alerts_invalid_parameters(client):
    """Test alert listing with invalid parameter types"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    # Test invalid UUID
    invalid_uuid_params = {
        "user_id": "not-a-uuid",
    }
    response = client.get("/api/v1/alerts/", params=invalid_uuid_params)
    assert response.status_code == 400
    assert "Invalid user_id format" in response.json()["detail"]
    
    # Test invalid offset/limit
    invalid_pagination_params = {
        "user_id": user_data["id"],
        "offset": -1,
        "limit": 101
    }
    response = client.get("/api/v1/alerts/", params=invalid_pagination_params)
    assert response.status_code == 400
    assert "Invalid pagination parameters" in response.json()["detail"]
    
    # Test invalid URL
    invalid_url_params = {
        "user_id": user_data["id"],
        "base_url": "not-a-valid-url"
    }
    response = client.get("/api/v1/alerts/", params=invalid_url_params)
    assert response.status_code == 400
    assert "Invalid base_url format" in response.json()["detail"]
    
    # Test invalid datetime format
    invalid_datetime_params = {
        "user_id": user_data["id"],
        "created_at": "not-a-datetime"
    }
    response = client.get("/api/v1/alerts/", params=invalid_datetime_params)
    assert response.status_code == 400
    assert "Invalid datetime format" in response.json()["detail"]

def test_list_alerts_minimal_parameters(client):
    """Test alert listing with only required parameters"""
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    # Only required user_id parameter
    minimal_params = {
        "user_id": user_data["id"]
    }
    
    response = client.get("/api/v1/alerts/", params=minimal_params)
    assert response.status_code == 200
    
    # Validate response
    data = response.json()
    AlertPromptListResponse.model_validate(data)

def test_cancel_alert_successful(client):
    """Test successful alert cancellation"""
    # First create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    # Create an alert first
    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/crypto-alert",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 50001, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    create_response = client.post("/api/v1/alerts/", json=alert_data)
    assert create_response.status_code == 201
    alert_id = create_response.json()["id"]
    
    # Now cancel the alert
    cancel_data = {
        "alert_id": alert_id,
        "user_id": user_data["id"]
    }
    
    response = client.post("/api/v1/alerts/cancel", json=cancel_data)
    assert response.status_code == 200
    
    # Verify the alert is now cancelled by getting it
    list_params = {
        "user_id": user_data["id"]
    }
    list_response = client.get("/api/v1/alerts/", params=list_params)
    assert list_response.status_code == 200
    alerts = list_response.json()["alerts"]
    cancelled_alert = next(alert for alert in alerts if alert["id"] == alert_id)
    assert cancelled_alert["status"] == "CANCELLED"

def test_cancel_nonexistent_alert(client):
    """Test attempting to cancel an alert that doesn't exist"""
    # Create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    cancel_data = {
        "alert_id": str(uuid4()),  # Random non-existent UUID
        "user_id": user_data["id"]
    }
    
    response = client.post("/api/v1/alerts/cancel", json=cancel_data)
    assert response.status_code == 400
    assert "Alert not found" in response.json()["detail"]

def test_cancel_alert_wrong_user(client, mock_google_verify):
    """Test attempting to cancel an alert belonging to another user"""
    # Create first user and their alert
    signup1 = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token_1"}
    )
    user1_data = signup1.json()["agent_controller"]
    
    alert_data = {
        "api_key": user1_data["api_key"],
        "user_id": user1_data["id"],
        "prompt": "Test alert",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    create_response = client.post("/api/v1/alerts/", json=alert_data)
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
    
    # Try to cancel first user's alert with second user's ID
    cancel_data = {
        "alert_id": alert_id,
        "user_id": user2_data["id"]
    }
    
    response = client.post("/api/v1/alerts/cancel", json=cancel_data)
    assert response.status_code == 400
    assert "Alert does not belong to user" in response.json()["detail"]

def test_cancel_alert_invalid_uuid(client):
    """Test attempting to cancel an alert with invalid UUID format"""
    # Create a user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token"}
    )
    user_data = signup_response.json()["agent_controller"]
    
    cancel_data = {
        "alert_id": "not-a-valid-uuid",
        "user_id": user_data["id"]
    }
    
    response = client.post("/api/v1/alerts/cancel", json=cancel_data)
    assert response.status_code == 400
    assert "Invalid UUID format" in response.json()["detail"]
    

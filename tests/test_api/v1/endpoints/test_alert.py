from datetime import datetime, timedelta
import uuid
from app.schemas.alert_prompt import AlertPromptCreateSuccessResponse, AlertPromptListResponse, AlertPromptItem
from app.models.alert_prompt import AlertStatus
import pytest

@pytest.mark.asyncio
async def test_create_alert_successful(client, valid_user_with_credits, sample_llm_models):
    """Test successful alert creation with valid data"""
    user_data = valid_user_with_credits
        
    alert_data = {
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/crypto-alert",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 50001, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=300)).isoformat(),
        "llm_model": "gemini-2.5-pro"
    }
    
    response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": user_data["api_key"]},
        json=alert_data
    )
    
    print(response.status_code, response.json())
    assert response.status_code == 201
    AlertPromptCreateSuccessResponse.model_validate(response.json())

@pytest.mark.asyncio
async def test_create_alert_invalid_api_key(client):
    """Test alert creation with invalid API key"""
    alert_data = {
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test"
    }
    
    response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": "invalid_api_key"},
        json=alert_data
    )
    
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_mismatched_user_api_key(client, mock_google_verify):
    """Test alert creation with API key not owned by user"""
    mock_google_verify.return_value = {
        'email': 'test1@example.com',
        'sub': '12345',
        'name': 'Test User 1'
    }
    signup1 = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token_1"}
    )
    user1_data = signup1.json()["agent_controller"]

    mock_google_verify.return_value = {
        'email': 'test2@example.com',
        'sub': '67890',
        'name': 'Test User 2'
    }
    signup2 = await client.post(
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
    
    response = await client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_insufficient_credits(client, valid_user_with_credits):
    """Test alert creation with insufficient credits"""
    user_data = valid_user_with_credits
    
    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test"
    }
    
    response = await client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 401
    assert "Insufficient credits" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_invalid_url(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "not-a-valid-url"
    }

    response = await client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_invalid_parsed_intent(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "parsed_intent": "not-a-valid-json"
    }

    response = await client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "Invalid parsed_intent format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_invalid_example_response(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "example_response": "not-a-valid-json"
    }

    response = await client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "Invalid example_response format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_invalid_max_datetime(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    alert_data = {
        "api_key": user_data["api_key"],
        "user_id": user_data["id"],
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "max_datetime": (datetime.now() + timedelta(minutes=20)).isoformat(),
        "llm_model": "gemini-2.5-pro"
    }

    response = await client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "max_datetime must be at least 30 minutes in the future" in response.json()["detail"]

    alert_data["max_datetime"] = (datetime.now() + timedelta(days=400)).isoformat()
    response = await client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 400
    assert "max_datetime cannot be more than 1 year in the future" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_invalid_llm_model(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    alert_data = {
        "prompt": "Test prompt",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "llm_model": "nonexistent_model_name"
    }

    response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": user_data["api_key"]},
        json=alert_data
    )

    assert response.status_code == 400
    assert "Invalid LLM model" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_alerts_successful(client, valid_user_with_credits):
    """Test successful alert listing with valid parameters"""
    user_data = valid_user_with_credits

    list_params = {
        "offset": 0,
        "limit": 50,
        "prompt_contains": "bitcoin",
        "created_after": datetime.now().isoformat(),
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat(),
        "llm_model": "gemini-2.5-pro"
    }
    
    response = await client.get(
        "/api/v1/alerts/",
        params=list_params,
        headers={"X-API-Key": user_data["api_key"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    AlertPromptListResponse.model_validate(data)

@pytest.mark.asyncio
async def test_list_alerts_invalid_parameters(client, valid_user_with_credits):
    """Test alert listing with invalid parameter types"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    invalid_pagination_params = {
        "offset": -1,
        "limit": 101
    }
    response = await client.get(
        "/api/v1/alerts/",
        params=invalid_pagination_params,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 400
    assert "Invalid pagination parameters" in response.json()["detail"]
    
    invalid_datetime_params = {
        "created_after": "not-a-datetime"
    }
    response = await client.get(
        "/api/v1/alerts/",
        params=invalid_datetime_params,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 400
    assert "Invalid datetime format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_alerts_datetime_validation(client, valid_user_with_credits):
    """Test datetime validation between created_after and max_datetime"""
    user_data = valid_user_with_credits
    
    now = datetime.now()
    params = {
        "created_after": (now + timedelta(days=2)).isoformat(),
        "max_datetime": (now + timedelta(days=1)).isoformat()
    }
    
    response = await client.get(
        "/api/v1/alerts/",
        params=params,
        headers={"X-API-Key": user_data["api_key"]}
    )
    assert response.status_code == 400
    assert "created_after cannot be later than max_datetime" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_alerts_minimal_parameters(client, valid_user_with_credits):
    """Test alert listing with no parameters (just authentication)"""
    user_data = valid_user_with_credits
    
    response = await client.get(
        "/api/v1/alerts/",
        headers={"X-API-Key": user_data["api_key"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    AlertPromptListResponse.model_validate(data)

@pytest.mark.asyncio
async def test_list_alerts_invalid_api_key(client):
    """Test alert listing with invalid API key"""
    response = await client.get(
        "/api/v1/alerts/",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_alert_successful(client, valid_user_with_credits):
    """Test successful alert retrieval"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    # Create an alert first
    alert_data = {
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/crypto-alert",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 50001, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat(),
        "llm_model": "gemini-2.5-pro"
    }
    
    create_response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key},
        json=alert_data
    )
    
    assert create_response.status_code == 201
    alert_id = create_response.json()["id"]
    
    response = await client.get(
        f"/api/v1/alerts/{alert_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    alert = response.json()
    
    AlertPromptItem.model_validate(alert)
    
    assert alert["prompt"] == alert_data["prompt"]
    assert alert["http_method"] == alert_data["http_method"]
    assert alert["http_url"] == alert_data["http_url"]

@pytest.mark.asyncio
async def test_get_alert_not_found(client, valid_user_with_credits):
    """Test attempting to get a non-existent alert"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    non_existent_id = str(uuid.uuid4())
    response = await client.get(
        f"/api/v1/alerts/{non_existent_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_alert_successful(client, valid_user_with_credits):
    """Test successful alert cancellation"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    # Create an alert first
    alert_data = {
        "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/crypto-alert",
        "parsed_intent": {"price_threshold": 50000, "currency": "BTC"},
        "example_response": {"price": 50001, "alert": True},
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat(),
        "llm_model": "gemini-2.5-pro"
    }
    
    create_response = await client.post(
        "/api/v1/alerts/", 
        headers={"X-API-Key": api_key},
        json=alert_data
    )
    
    assert create_response.status_code == 201
    alert_id = create_response.json()["id"]
    
    # Now cancel the alert using PATCH
    response = await client.patch(
        f"/api/v1/alerts/{alert_id}/cancel",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    
    # Verify the alert is now cancelled by getting it
    list_response = await client.get(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key}
    )
    assert list_response.status_code == 200
    alerts = list_response.json()["alerts"]
    cancelled_alert = next(alert for alert in alerts if alert["id"] == alert_id)
    assert cancelled_alert["status"] == AlertStatus.CANCELLED

@pytest.mark.asyncio
async def test_cancel_alert_invalid_api_key(client):
    """Test attempting to cancel an alert with invalid API key"""
    
    response = await client.patch(
        f"/api/v1/alerts/{str(uuid.uuid4())}/cancel",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 403
    assert "Unauthorized" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_alert_wrong_user(client, valid_user_with_credits, mock_google_verify):
    """Test attempting to cancel an alert belonging to another user"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    alert_data = {
        "prompt": "Test alert",
        "http_method": "POST",
        "http_url": "https://webhook.example.com/test",
        "max_datetime": (datetime.now() + timedelta(days=30)).isoformat(),
        "llm_model": "gemini-2.5-pro",
        "parsed_intent": {"foo": "bar"},
        "example_response": {"foo": "bar"}
    }
    
    create_response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key},
        json=alert_data
    )
    alert_id = create_response.json()["id"]
    
    mock_google_verify.return_value = {
        'email': 'test2@example.com',
        'sub': '67890',
        'name': 'Test User 2'
    }
    signup2 = await client.post(
        "/api/v1/auth/signup",
        json={"access_token": "valid_google_token_2"}
    )
    user2_data = signup2.json()["agent_controller"]
    api_key2 = user2_data["api_key"]
    
    response = await client.patch(
        f"/api/v1/alerts/{alert_id}/cancel",
        headers={"X-API-Key": api_key2}
    )
    
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_nonexistent_alert(client, valid_user_with_credits):
    """Test attempting to cancel an alert that doesn't exist"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    response = await client.patch(
        f"/api/v1/alerts/{str(uuid.uuid4())}/cancel",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

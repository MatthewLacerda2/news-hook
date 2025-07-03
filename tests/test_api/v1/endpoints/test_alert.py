import uuid
import pytest
from datetime import datetime, timedelta
from app.models.agent_controller import AgentController
from app.schemas.alert_prompt import AlertPromptCreateSuccessResponse, AlertPromptListResponse, AlertPromptItem
from pydantic import BaseModel

class TestPayload(BaseModel):
    price: int
    date: datetime
    currency: str
test_alert_data = {
    "prompt": "Monitor Bitcoin price and alert if it goes above $50,000",
    "http_method": "POST",
    "http_url": "https://webhook.example.com/crypto-alert",
    "http_headers": {
        "Content-Type": "application/json"
    },
    "llm_model": "gemini-2.5-pro",
    "max_datetime": (datetime.now() + timedelta(days=300)).isoformat(),
    "is_recurring": False,
}

@pytest.mark.asyncio
async def test_create_alert_successful(client, valid_user_with_credits, sample_llm_models, test_db, mock_llm_validation):
    """Test successful alert creation with valid data"""
    user_data = valid_user_with_credits

    response = await client.post(
        "/api/v1/alerts/",
        json=test_alert_data,
        headers={"X-API-Key": user_data["api_key"]}
    )
    
    print(response)
    print(response.json())
    print(response.status_code)
    
    assert response.status_code == 201
    AlertPromptCreateSuccessResponse.model_validate(response.json())
    assert mock_llm_validation.called

@pytest.mark.asyncio
async def test_create_alert_invalid_api_key(client, test_db):
    """Test alert creation with invalid API key"""
    
    response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": "invalid_api_key"},
        json=test_alert_data
    )
    
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_mismatched_user_api_key(client, mock_google_verify, test_db):
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
    alert_data = test_alert_data
    alert_data["api_key"] = user1_data["api_key"]
    alert_data["user_id"] = user2_data["id"]    
    
    response = await client.post("/api/v1/alerts/", json=alert_data)
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_insufficient_credits(client, valid_user_with_credits, test_db):
    """Test alert creation with insufficient credits"""
    user_data = valid_user_with_credits

    user = await test_db.get(AgentController, user_data["id"])
    user.credit_balance = 0
    await test_db.commit()
    await test_db.refresh(user)

    response = await client.post(
        "/api/v1/alerts/",
        json={
            "user_id": user_data["id"],
            "prompt": "Test prompt",
            "http_method": "POST",
            "http_url": "https://webhook.example.com/test",
            "is_recurring": False
        },
        headers={"X-API-Key": user_data["api_key"]}
    )
    assert response.status_code == 403
    assert "Insufficient credits" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_alert_invalid_max_datetime(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    alert_data = test_alert_data
    alert_data["max_datetime"] = (datetime.now() + timedelta(days=365)).isoformat()
    
    response = await client.post("/api/v1/alerts/", json=alert_data, headers={"X-API-Key": user_data["api_key"]})
    
    assert response.status_code == 422
    assert any(
        "max_datetime cannot be more than 300 days in the future" in err["msg"]
        for err in response.json()["detail"]
    )

@pytest.mark.asyncio
async def test_create_alert_invalid_llm_model(client, valid_user_with_credits, sample_llm_models, test_db, mock_llm_validation):
    user_data = valid_user_with_credits

    alert_data = test_alert_data
    alert_data["llm_model"] = "not-a-valid-llm-model"

    response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": user_data["api_key"]},
        json=alert_data
    )

    assert response.status_code == 400
    assert "Invalid LLM model" in response.json()["detail"]
    assert not mock_llm_validation.called

@pytest.mark.asyncio
async def test_list_alerts_successful(client, valid_user_with_credits):
    """Test successful alert listing with valid parameters"""

    list_params = {
        "offset": 0,
        "limit": 50,
        "prompt_contains": "bitcoin",
        "created_after": datetime.now().isoformat(),
        "max_datetime": (datetime.now() + timedelta(days=300)).isoformat(),
        "llm_model": "gemini-2.5-pro"
    }
    
    response = await client.get(
        "/api/v1/alerts/",
        params=list_params,
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    AlertPromptListResponse.model_validate(data)

@pytest.mark.asyncio
async def test_list_alerts_invalid_parameters(client, valid_user_with_credits, test_db, sample_llm_models):
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
    assert response.status_code == 422
    assert any(
        "greater than or equal to 0" in error["msg"] or
        "less than or equal to 100" in error["msg"]
        for error in response.json()["detail"]
    )
    
    invalid_datetime_params = {
        "created_after": "not-a-datetime"
    }
    response = await client.get(
        "/api/v1/alerts/",
        params=invalid_datetime_params,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 422
    assert any(
        "valid datetime" in error["msg"] or "invalid datetime format" in error["msg"]
        for error in response.json()["detail"]
    )

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
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 400
    assert "created_after cannot be later than max_datetime" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_alerts_minimal_parameters(client, valid_user_with_credits):
    """Test alert listing with no parameters (just authentication)"""
    user_data = valid_user_with_credits
    
    response = await client.get(
        "/api/v1/alerts/",
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    AlertPromptListResponse.model_validate(data)

@pytest.mark.asyncio
async def test_list_alerts_invalid_api_key(client, test_db):
    """Test alert listing with invalid API key"""
    response = await client.get(
        "/api/v1/alerts/",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]
    
@pytest.mark.asyncio
async def test_get_alert_invalid_api_key(client, test_db):
    """Test alert retrieval with invalid API key"""
    response = await client.get(
        "/api/v1/alerts/123",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]
    
@pytest.mark.asyncio
async def test_get_alert_successful(client, valid_user_with_credits, sample_llm_models, test_db, mock_llm_validation):
    """Test successful alert retrieval"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    create_response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key},
        json=test_alert_data
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
    
    assert alert["prompt"] == test_alert_data["prompt"]
    assert alert["http_method"] == test_alert_data["http_method"]
    assert alert["http_url"] == test_alert_data["http_url"]

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
async def test_cancel_alert_successful(client, valid_user_with_credits, sample_llm_models, test_db, mock_llm_validation):
    """Test successful alert cancellation"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    create_response = await client.post(
        "/api/v1/alerts/", 
        json=test_alert_data,
        headers={"X-API-Key": api_key}
    )
    
    assert create_response.status_code == 201
    alert_id = create_response.json()["id"]
    assert mock_llm_validation.called
    
    response = await client.patch(
        f"/api/v1/alerts/{alert_id}/cancel",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    
    list_response = await client.get(
        f"/api/v1/alerts/{alert_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert list_response.status_code == 200
    alert = list_response.json()
    assert alert["id"] == alert_id
    assert alert["status"] == "CANCELLED"

@pytest.mark.asyncio
async def test_cancel_alert_invalid_api_key(client, test_db):
    """Test attempting to cancel an alert with invalid API key"""
    
    response = await client.patch(
        f"/api/v1/alerts/{str(uuid.uuid4())}/cancel",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_alert_wrong_user(client, valid_user_with_credits, mock_google_verify, sample_llm_models, test_db, mock_llm_validation):
    """Test attempting to cancel an alert belonging to another user"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
        
    create_response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key},
        json=test_alert_data
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

@pytest.mark.asyncio
async def test_patch_alert_invalid_api_key(client, test_db):
    """Test patching an alert with invalid API key"""
    response = await client.patch(
        "/api/v1/alerts/123",
        headers={"X-API-Key": "invalid_api_key"},
        json={"http_url": "https://new-webhook.example.com"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_patch_alert_not_found(client, valid_user_with_credits):
    """Test patching a non-existent alert"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    non_existent_id = str(uuid.uuid4())
    response = await client.patch(
        f"/api/v1/alerts/{non_existent_id}",
        headers={"X-API-Key": api_key},
        json={"http_url": "https://new-webhook.example.com"}
    )
    
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_patch_alert_successful(client, valid_user_with_credits, sample_llm_models, test_db, mock_llm_validation):
    """Test successful alert patching and validate changes"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    # First create an alert
    create_response = await client.post(
        "/api/v1/alerts/",
        headers={"X-API-Key": api_key},
        json=test_alert_data
    )
    
    assert create_response.status_code == 201
    alert_id = create_response.json()["id"]
    
    # Patch data to update
    patch_data = {
        "http_url": "https://new-webhook.example.com/updated",
        "http_headers": {"Content-Type": "application/json", "Authorization": "Bearer token123"},
        "is_recurring": True,
        "http_method": "PUT",
        "llm_model": "gemini-2.0-flash",
        "max_datetime": (datetime.now() + timedelta(days=200)).isoformat()
    }
    
    # Patch the alert
    patch_response = await client.patch(
        f"/api/v1/alerts/{alert_id}",
        headers={"X-API-Key": api_key},
        json=patch_data
    )
    
    assert patch_response.status_code == 200
    patched_alert = patch_response.json()
    
    # Validate the response schema
    AlertPromptItem.model_validate(patched_alert)
    
    # Verify the changes were applied
    assert patched_alert["http_url"] == patch_data["http_url"]
    assert patched_alert["http_headers"] == patch_data["http_headers"]
    assert patched_alert["is_recurring"] == patch_data["is_recurring"]
    assert patched_alert["http_method"] == patch_data["http_method"]
    assert patched_alert["llm_model"] == patch_data["llm_model"]
    assert patched_alert["max_datetime"] == patch_data["max_datetime"]
        
    # Verify the changes persist by getting the alert again
    get_response = await client.get(
        f"/api/v1/alerts/{alert_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert get_response.status_code == 200
    retrieved_alert = get_response.json()
    
    # Verify all changes are still there
    assert retrieved_alert["http_url"] == patch_data["http_url"]
    assert retrieved_alert["http_headers"] == patch_data["http_headers"]
    assert retrieved_alert["is_recurring"] == patch_data["is_recurring"]
    assert retrieved_alert["http_method"] == patch_data["http_method"]
    assert retrieved_alert["llm_model"] == patch_data["llm_model"]
    assert retrieved_alert["max_datetime"] == patch_data["max_datetime"]
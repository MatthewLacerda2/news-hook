import uuid
import pytest
from datetime import datetime, timedelta
from app.models.agent_controller import AgentController
from app.models.notification import Notification
from app.schemas.notification import NotificationCreateSuccessResponse, NotificationListResponse, NotificationItem
from pydantic import BaseModel
from app.utils.env import MAX_DATETIME

class TestPayload(BaseModel):
    price: int
    date: datetime
    currency: str
test_notification_data = {
    "prompt": "Monitor Bitcoin price and notification whenever it reaches a new record high",
    "http_method": "POST",
    "http_url": "https://webhook.example.com/crypto-notification",
    "http_headers": {
        "Content-Type": "application/json"
    },
    "payload_format": TestPayload.model_json_schema(),
    "llm_model": "llama3.1",
    "max_datetime": (datetime.now() + timedelta(days=MAX_DATETIME)).isoformat(),
}

@pytest.mark.asyncio
async def test_create_notification_successful(client, valid_user_with_credits, sample_llm_models, test_db):
    """Test successful notification creation with valid data"""
    user_data = valid_user_with_credits

    response = await client.post(
        "/api/v1/notifications/",
        json=test_notification_data,
        headers={"X-API-Key": user_data["api_key"]}
    )
    
    print(response)
    print(response.json())
    print(response.status_code)
    
    assert response.status_code == 201
    NotificationCreateSuccessResponse.model_validate(response.json())

@pytest.mark.asyncio
async def test_create_notification_invalid_api_key(client, test_db):
    """Test notification creation with invalid API key"""
    
    response = await client.post(
        "/api/v1/notification/",
        headers={"X-API-Key": "invalid_api_key"},
        json=test_notification_data
    )
    
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_notification_mismatched_user_api_key(client, mock_google_verify, test_db):
    """Test notification creation with API key not owned by user"""
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
    
    # Try to create notification with user1's API key but user2's ID
    notification_data = test_notification_data
    notification_data["api_key"] = user1_data["api_key"]
    notification_data["user_id"] = user2_data["id"]    
    
    response = await client.post("/api/v1/notification/", json=notification_data)
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_notification_insufficient_credits(client, valid_user_with_credits, test_db):
    """Test notification creation with insufficient credits"""
    user_data = valid_user_with_credits

    user = await test_db.get(AgentController, user_data["id"])
    user.credit_balance = 0
    await test_db.commit()
    await test_db.refresh(user)

    response = await client.post(
        "/api/v1/notification/",
        json={
            "user_id": user_data["id"],
            "prompt": "Test prompt",
            "http_method": "POST",
            "http_url": "https://webhook.example.com/test"
        },
        headers={"X-API-Key": user_data["api_key"]}
    )
    assert response.status_code == 403
    assert "Insufficient credits" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_notification_invalid_url(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    notification_data = test_notification_data
    notification_data["user_id"] = user_data["id"]
    notification_data["http_url"] = "not-a-valid-url"

    response = await client.post("/api/v1/notification/", json=notification_data, headers={"X-API-Key": user_data["api_key"]})
    assert response.status_code == 422
    assert any(
        "valid URL" in error["msg"] for error in response.json()["detail"]
    )

@pytest.mark.asyncio
async def test_create_notification_invalid_payload_format(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    notification_data = test_notification_data
    notification_data["payload_format"] = "not-a-valid-json"

    response = await client.post("/api/v1/notification/", json=notification_data, headers={"X-API-Key": user_data["api_key"]})
    assert response.status_code == 422
    
    # Print the actual error message for debugging
    print("\nActual error response:", response.json()["detail"])
    
    assert any(
        "payload_format must be a valid dictionary" in error["msg"] for error in response.json()["detail"]
    )

@pytest.mark.asyncio
async def test_create_notification_invalid_max_datetime(client, valid_user_with_credits):
    user_data = valid_user_with_credits

    notification_data = test_notification_data
    notification_data["max_datetime"] = (datetime.now() + timedelta(days=MAX_DATETIME)).isoformat()
    
    response = await client.post("/api/v1/notification/", json=notification_data, headers={"X-API-Key": user_data["api_key"]})
    
    assert response.status_code == 422
    assert any(
        "max_datetime cannot be more than 365 days in the future" in err["msg"]
        for err in response.json()["detail"]
    )

@pytest.mark.asyncio
async def test_create_notification_invalid_llm_model(client, valid_user_with_credits, sample_llm_models, test_db):
    user_data = valid_user_with_credits

    notification_data = test_notification_data
    notification_data["llm_model"] = "not-a-valid-llm-model"

    response = await client.post(
        "/api/v1/notification/",
        headers={"X-API-Key": user_data["api_key"]},
        json=notification_data
    )

    assert response.status_code == 400
    assert "Invalid LLM model" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_notifications_successful(client, valid_user_with_credits):
    """Test successful notification listing with valid parameters"""

    list_params = {
        "offset": 0,
        "limit": 50,
        "prompt_contains": "bitcoin",
        "created_after": datetime.now().isoformat(),
        "max_datetime": (datetime.now() + timedelta(days=MAX_DATETIME)).isoformat(),
        "llm_model": "llama3.1"
    }
    
    response = await client.get(
        "/api/v1/notification/",
        params=list_params,
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    NotificationListResponse.model_validate(data)

@pytest.mark.asyncio
async def test_list_notifications_invalid_parameters(client, valid_user_with_credits, test_db, sample_llm_models):
    """Test notification listing with invalid parameter types"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    invalid_pagination_params = {
        "offset": -1,
        "limit": 101
    }
    response = await client.get(
        "/api/v1/notification/",
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
        "/api/v1/notification/",
        params=invalid_datetime_params,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 422
    assert any(
        "valid datetime" in error["msg"] or "invalid datetime format" in error["msg"]
        for error in response.json()["detail"]
    )

@pytest.mark.asyncio
async def test_list_notifications_datetime_validation(client, valid_user_with_credits):
    """Test datetime validation between created_after and max_datetime"""
    user_data = valid_user_with_credits
    
    now = datetime.now()
    params = {
        "created_after": (now + timedelta(days=2)).isoformat(),
        "max_datetime": (now + timedelta(days=1)).isoformat()
    }
    
    response = await client.get(
        "/api/v1/notification/",
        params=params,
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 400
    assert "created_after cannot be later than max_datetime" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_notifications_minimal_parameters(client, valid_user_with_credits):
    """Test notification listing with no parameters (just authentication)"""
    
    response = await client.get(
        "/api/v1/notification/",
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    NotificationListResponse.model_validate(data)

@pytest.mark.asyncio
async def test_list_notifications_invalid_api_key(client, test_db):
    """Test notification listing with invalid API key"""
    response = await client.get(
        "/api/v1/notification/",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]
    
@pytest.mark.asyncio
async def test_get_notification_invalid_api_key(client, test_db):
    """Test notification retrieval with invalid API key"""
    response = await client.get(
        "/api/v1/notification/123",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]
    
@pytest.mark.asyncio
async def test_get_notification_successful(client, valid_user_with_credits, sample_llm_models, test_db):
    """Test successful notification retrieval"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    create_response = await client.post(
        "/api/v1/notification/",
        headers={"X-API-Key": api_key},
        json=test_notification_data
    )
    
    assert create_response.status_code == 201
    notification_id = create_response.json()["id"]
    
    response = await client.get(
        f"/api/v1/notification/{notification_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    notification = response.json()
    
    NotificationItem.model_validate(notification)
    
    assert notification["prompt"] == test_notification_data["prompt"]
    assert notification["http_method"] == test_notification_data["http_method"]
    assert notification["http_url"] == test_notification_data["http_url"]

@pytest.mark.asyncio
async def test_get_notification_not_found(client, valid_user_with_credits):
    """Test attempting to get a non-existent notification"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    non_existent_id = str(uuid.uuid4())
    response = await client.get(
        f"/api/v1/notification/{non_existent_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_notification_successful(client, valid_user_with_credits, sample_llm_models, test_db):
    """Test successful notification cancellation"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    create_response = await client.post(
        "/api/v1/notification/", 
        json=test_notification_data,
        headers={"X-API-Key": api_key}
    )
    
    assert create_response.status_code == 201
    notification_id = create_response.json()["id"]
    
    # Now cancel the notification using PATCH
    response = await client.patch(
        f"/api/v1/notification/{notification_id}/cancel",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 200
    
    # Verify the notification is now cancelled by getting it
    list_response = await client.get(
        f"/api/v1/notification/{notification_id}",
        headers={"X-API-Key": api_key}
    )
    
    assert list_response.status_code == 200
    notification = list_response.json()
    assert notification["id"] == notification_id
    assert notification["status"] == "CANCELLED"

@pytest.mark.asyncio
async def test_cancel_notification_invalid_api_key(client, test_db):
    """Test attempting to cancel an notification with invalid API key"""
    
    response = await client.patch(
        f"/api/v1/notification/{str(uuid.uuid4())}/cancel",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_notification_wrong_user(client, valid_user_with_credits, mock_google_verify, sample_llm_models, test_db):
    """Test attempting to cancel an notification belonging to another user"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
        
    create_response = await client.post(
        "/api/v1/notification/",
        headers={"X-API-Key": api_key},
        json=test_notification_data
    )
    notification_id = create_response.json()["id"]
    
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
        f"/api/v1/notification/{notification_id}/cancel",
        headers={"X-API-Key": api_key2}
    )
    
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cancel_nonexistent_notification(client, valid_user_with_credits):
    """Test attempting to cancel an notification that doesn't exist"""
    user_data = valid_user_with_credits
    api_key = user_data["api_key"]
    
    response = await client.patch(
        f"/api/v1/notification/{str(uuid.uuid4())}/cancel",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 404
    assert "Not found" in response.json()["detail"]

#test_list_events

import pytest
from datetime import datetime, timedelta

from app.schemas.alert_event import AlertEventListResponse

@pytest.mark.asyncio
async def test_list_events_successful(client, valid_user_with_credits):
    """Test successful event listing with valid parameters"""
    list_params = {
        "offset": 0,
        "limit": 50,
        "triggered_after": datetime.now().isoformat(),
        "triggered_before": (datetime.now() + timedelta(days=300)).isoformat()
    }
    
    response = await client.get(
        "/api/v1/events/",
        params=list_params,
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    AlertEventListResponse.model_validate(data)
    
    # Verify the response structure
    assert "events" in data
    assert "total_count" in data
    
    # If there are events, verify they have all required fields
    if data["events"]:
        event = data["events"][0]
        required_fields = {
            "id", "alert_prompt_id", "triggered_at", "structured_data",
            "prompt", "http_method", "http_url", "is_recurring"
        }
        assert all(field in event for field in required_fields)

@pytest.mark.asyncio
async def test_list_events_invalid_parameters(client, valid_user_with_credits, test_db):
    """Test event listing with invalid parameter types"""
    api_key = valid_user_with_credits["api_key"]
    
    # Test invalid pagination parameters
    invalid_pagination_params = {
        "offset": -1,
        "limit": 101
    }
    response = await client.get(
        "/api/v1/events/",
        params=invalid_pagination_params,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 422
    assert any(
        "greater than or equal to 0" in error["msg"] or
        "less than or equal to 100" in error["msg"]
        for error in response.json()["detail"]
    )
    
    # Test invalid datetime parameters
    invalid_datetime_params = {
        "triggered_after": "not-a-datetime"
    }
    response = await client.get(
        "/api/v1/events/",
        params=invalid_datetime_params,
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 422
    assert any(
        "valid datetime" in error["msg"] or "invalid datetime format" in error["msg"]
        for error in response.json()["detail"]
    )

@pytest.mark.asyncio
async def test_list_events_datetime_validation(client, valid_user_with_credits):
    """Test datetime validation between triggered_after and triggered_before"""
    now = datetime.now()
    params = {
        "triggered_after": (now + timedelta(days=2)).isoformat(),
        "triggered_before": (now + timedelta(days=1)).isoformat()
    }
    
    response = await client.get(
        "/api/v1/events/",
        params=params,
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 400
    assert "triggered_after cannot be later than triggered_before" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_events_minimal_parameters(client, valid_user_with_credits):
    """Test event listing with no parameters (just authentication)"""
    response = await client.get(
        "/api/v1/events/",
        headers={"X-API-Key": valid_user_with_credits["api_key"]}
    )
    assert response.status_code == 200
    
    data = response.json()
    AlertEventListResponse.model_validate(data)

@pytest.mark.asyncio
async def test_list_events_invalid_api_key(client, test_db):
    """Test event listing with invalid API key"""
    response = await client.get(
        "/api/v1/events/",
        headers={"X-API-Key": "invalid_api_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

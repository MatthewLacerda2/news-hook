import pytest

@pytest.mark.asyncio
async def test_post_document_success(client, valid_user_with_credits):
    """Test successful document upload with valid data"""
    user = valid_user_with_credits
    doc_data = {
        "name": "My Document",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": user["api_key"], "X-User-Id": user["id"]}
    response = await client.post(
        "/api/v1/documents/",
        json=doc_data,
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == doc_data["name"]
    assert data["created_at"] is not None

@pytest.mark.asyncio
async def test_post_document_invalid_name(client, valid_user_with_credits):
    """Test document upload with name too short"""
    user = valid_user_with_credits
    doc_data = {
        "name": "ab",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": user["api_key"], "X-User-Id": user["id"]}
    response = await client.post(
        "/api/v1/documents/",
        json=doc_data,
        headers=headers
    )
    assert response.status_code == 401
    assert "name" in response.json()["detail"]

@pytest.mark.asyncio
async def test_post_document_invalid_content(client, valid_user_with_credits):
    """Test document upload with content too short"""
    user = valid_user_with_credits
    doc_data = {
        "name": "Valid Name",
        "content": "Too short"
    }
    headers = {"X-API-Key": user["api_key"], "X-User-Id": user["id"]}
    response = await client.post(
        "/api/v1/documents/",
        json=doc_data,
        headers=headers
    )
    assert response.status_code == 401
    assert "content" in response.json()["detail"]

@pytest.mark.asyncio
async def test_post_document_invalid_api_key(client, valid_user_with_credits):
    """Test document upload with invalid API key for user"""
    user = valid_user_with_credits
    doc_data = {
        "name": "Valid Name",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": "invalid_api_key", "X-User-Id": user["id"]}
    response = await client.post(
        "/api/v1/documents/",
        json=doc_data,
        headers=headers
    )
    assert response.status_code == 401
    assert "api_key" in response.json()["detail"] or "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_post_document_mismatched_user_api_key(client, mock_google_verify, test_db):
    """Test document upload with API key not owned by user_id"""
    # Create user 1
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

    # Create user 2
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

    # Try to post document with user1's API key but user2's user_id
    doc_data = {
        "name": "Valid Name",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": user1_data["api_key"], "X-User-Id": user2_data["id"]}
    response = await client.post(
        "/api/v1/documents/",
        json=doc_data,
        headers=headers
    )
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"] or "mismatch" in response.json()["detail"]
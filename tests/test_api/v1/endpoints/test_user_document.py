import pytest
import uuid

@pytest.mark.asyncio
async def test_post_user_document_success(client, valid_user_with_credits):
    """Test successful document upload with valid data"""
    user = valid_user_with_credits
    doc_data = {
        "name": "My Document",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": user["api_key"], "X-User-Id": user["id"]}
    response = await client.post(
        "/api/v1/user_documents/",
        json=doc_data,
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == doc_data["name"]
    assert data["created_at"] is not None

@pytest.mark.asyncio
async def test_post_user_document_invalid_api_key(client, valid_user_with_credits):
    """Test document upload with invalid API key for user"""
    user = valid_user_with_credits
    doc_data = {
        "name": "Valid Name",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": "invalid_api_key", "X-User-Id": user["id"]}
    response = await client.post(
        "/api/v1/user_documents/",
        json=doc_data,
        headers=headers
    )
    assert response.status_code == 401
    assert "api_key" in response.json()["detail"] or "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_post_user_document_mismatched_user_api_key(client, mock_google_verify, test_db):
    """Test document upload with API key not owned by user_id"""
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

    # Try to post document with user1's API key but user2's user_id
    doc_data = {
        "name": "Valid Name",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": user1_data["api_key"], "X-User-Id": user2_data["id"]}
    response = await client.post(
        "/api/v1/user_documents/",
        json=doc_data,
        headers=headers
    )
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"] or "mismatch" in response.json()["detail"]
    
#tests for get document start here

@pytest.mark.asyncio
async def test_get_user_document_success(client, valid_user_with_credits):
    """Test successful document retrieval with valid data"""
    user = valid_user_with_credits
    # First create a document
    doc_data = {
        "name": "My Document",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": user["api_key"], "X-User-Id": user["id"]}
    create_response = await client.post(
        "/api/v1/user_documents/",
        json=doc_data,
        headers=headers
    )
    created_doc = create_response.json()
    
    # Now try to get the document
    response = await client.get(
        f"/api/v1/user_documents/{created_doc['id']}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_doc["id"]
    assert data["name"] == doc_data["name"]
    assert data["content"] == doc_data["content"]

@pytest.mark.asyncio
async def test_get_user_document_invalid_api_key(client, valid_user_with_credits):
    """Test document retrieval with invalid API key"""
    user = valid_user_with_credits
    # First create a document
    doc_data = {
        "name": "My Document",
        "content": "This is a sufficiently long document content."
    }
    headers = {"X-API-Key": user["api_key"], "X-User-Id": user["id"]}
    create_response = await client.post(
        "/api/v1/user_documents/",
        json=doc_data,
        headers=headers
    )
    created_doc = create_response.json()
    
    # Try to get with invalid API key
    invalid_headers = {"X-API-Key": "invalid_key", "X-User-Id": user["id"]}
    response = await client.get(
        f"/api/v1/user_documents/{created_doc['id']}",
        headers=invalid_headers
    )
    assert response.status_code == 401
    assert "api_key" in response.json()["detail"] or "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_user_document_not_found(client, valid_user_with_credits):
    """Test document retrieval with non-existent document ID"""
    user = valid_user_with_credits
    headers = {"X-API-Key": user["api_key"], "X-User-Id": user["id"]}
    
    non_existent_id = str(uuid.uuid4())  # Generate a random UUID that won't exist
    response = await client.get(
        f"/api/v1/user_documents/{non_existent_id}",
        headers=headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
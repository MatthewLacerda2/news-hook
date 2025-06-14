import pytest
import uuid
from app.schemas.user_document import UserDocumentListResponse

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
async def test_get_user_document_success(client, valid_user_with_credits):
    """Test successful document retrieval with valid data"""
    user = valid_user_with_credits
    
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
    
    non_existent_id = str(uuid.uuid4())
    response = await client.get(
        f"/api/v1/user_documents/{non_existent_id}",
        headers=headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
@pytest.mark.asyncio
async def test_get_user_documents_success(client, valid_user_with_credits):
    """Test successful document listing with valid data"""    
    user = valid_user_with_credits    
    headers = {"X-API-Key": user["api_key"], "X-User-Id": user["id"]}
    doc_data = [
        {
            "name": f"My Document {i} exampletext",
            "content": f"This is a sufficiently long document content {i}."
        }
        for i in range(2)
    ]
    for doc in doc_data:
        await client.post(
            "/api/v1/user_documents/",
            json=doc,
            headers=headers
        )
    
    response = await client.get(
        "/api/v1/user_documents/?offset=1&limit=2&contains=exampletext",
        headers=headers
    )
    
    assert response.status_code == 200
    data = UserDocumentListResponse.model_validate(response.json())    
    assert "exampletext" in data.documents[0].name
    assert len(data.documents) == 1
    assert data.total_count == 1

@pytest.mark.asyncio
async def test_get_user_documents_invalid_api_key(client, valid_user_with_credits):
    """Test document listing with invalid API key"""
    user = valid_user_with_credits
    headers = {"X-API-Key": "invalid_key", "X-User-Id": user["id"]}
    
    response = await client.get(
        "/api/v1/user_documents/",
        headers=headers
    )
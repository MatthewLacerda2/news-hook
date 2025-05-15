import pytest
from app.schemas.llm_models import LLMModelListResponse

@pytest.mark.asyncio
async def test_list_llm_models(client, sample_llm_models):
    response = await client.get("/api/v1/llm-models/?actives_only=true")
    assert response.status_code == 200
    
    validated_data = LLMModelListResponse.model_validate(response.json())
    assert len(validated_data.items) == 2
    assert all(model.is_active for model in validated_data.items)
    
    response = await client.get("/api/v1/llm-models/?actives_only=false")
    assert response.status_code == 200
    
    validated_data = LLMModelListResponse.model_validate(response.json())
    assert len(validated_data.items) == 3

@pytest.mark.asyncio
async def test_list_llm_models_default(client, sample_llm_models):
    response = await client.get("/api/v1/llm-models/")
    assert response.status_code == 200
    
    validated_data = LLMModelListResponse.model_validate(response.json())
    assert len(validated_data.items) == 2
    assert all(model.is_active for model in validated_data.items)
    
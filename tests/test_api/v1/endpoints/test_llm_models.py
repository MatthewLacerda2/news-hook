import pytest
from app.schemas.llm_models import LLMModelListResponse

def test_list_llm_models(client, sample_llm_models):
    # Test with actives_only=True
    response = client.get("/api/v1/llm-models?actives_only=true")
    assert response.status_code == 200
    
    validated_data = LLMModelListResponse.model_validate(response.json())
    assert len(validated_data.items) == 2  # Should only return active models
    assert all(model.is_active for model in validated_data.items)
    
    # Test with actives_only=false
    response = client.get("/api/v1/llm-models?actives_only=false")
    assert response.status_code == 200
    
    validated_data = LLMModelListResponse.model_validate(response.json())
    assert len(validated_data.items) == 3  # Should return all models

# Test default behavior (should be the same as actives_only=true)
def test_list_llm_models_default(client, sample_llm_models):
    response = client.get("/api/v1/llm-models")
    assert response.status_code == 200
    
    validated_data = LLMModelListResponse.model_validate(response.json())
    assert len(validated_data.items) == 2  # Should only return active models by default
    assert all(model.is_active for model in validated_data.items)
    
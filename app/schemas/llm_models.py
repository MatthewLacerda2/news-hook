from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import List

class LLMModelItem(BaseModel):
    id: UUID
    model_name: str
    input_token_price: float
    output_token_price: float
    is_active: bool = Field(..., description="Whether the model is currently active and can be used")

    model_config = ConfigDict(from_attributes=True)

class LLMModelListResponse(BaseModel):
    items: List[LLMModelItem]

    model_config = ConfigDict(from_attributes=True)

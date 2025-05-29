from pydantic import BaseModel, Field, ConfigDict
from typing import List

class LLMModelItem(BaseModel):
    model_name: str = Field(..., description="The name of the LLM model. Vertex-AI refers to it as the model ID.")
    input_token_price: float = Field(..., description="Input token price in dollars per million tokens, without cache hit")
    output_token_price: float = Field(..., description="Output token price in dollars per million tokens, without cache hit")

    model_config = ConfigDict(from_attributes=True)

class LLMModelListResponse(BaseModel):
    items: List[LLMModelItem]

    model_config = ConfigDict(from_attributes=True)

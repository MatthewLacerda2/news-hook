from pydantic import BaseModel, Field
from typing import Dict, Union

JsonPrimitive = Union[str, int, float, bool, None]

class LLMValidationFormat(BaseModel):
    
    approval: bool = Field(default=False, description="Whether the alert's request is a valid one")
    chance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.")
    
    output_intent: str = Field(description="What the LLM understood from the alert request")
    keywords: list[str] = Field(description="The keywords that MUST be in the data that triggers the alert")
    
    def __init__(self, approval: bool, chance_score: float):
        self.approval = approval
        self.chance_score = chance_score


class LLMVerificationFormat(BaseModel):
    
    approval: bool = Field(default=False, description="Whether the document matches the alert's intent")
    chance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.")
    
    def __init__(self, approval: bool, chance_score: float):
        self.approval = approval
        self.chance_score = chance_score
        
class LLMGenerationFormat(BaseModel):
    
    output: str = Field(description="The LLM output on the matter")
    tags: list[str] = Field(description="The tags for the alert")
    structured_data: Dict[str, JsonPrimitive] = Field(description="The structured JSON response as requested by the alert requester")
    
    def __init__(self, output: str, tags: list[str], structured_data: Dict[str, JsonPrimitive]):
        self.output = output
        self.tags = tags
        self.structured_data = structured_data
from pydantic import BaseModel, Field
from typing import Dict, Any

class LLMValidationFormat(BaseModel):
    
    approval: bool = Field(default=False, description="Is the alert's request valid?")
    chance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimation of the quality of the request. Ranging from 0.0 to 1.0. Must be at least 0.85 to approve.")
    
    output_intent: Any = Field(description="What the LLM understood from the alert request")    #TODO: remove
    keywords: list[str] = Field(description="The keywords that MUST be in the data that triggers the alert")


class LLMVerificationFormat(BaseModel):
    
    approval: bool = Field(default=False, description="Whether the document matches the alert's intent")
    chance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.")
        
class LLMGenerationFormat(BaseModel):
    
    output: str = Field(description="The LLM output on the matter")
    tags: list[str] = Field(description="The tags for the alert")
    source_url: str = Field(description="The URL of the source that triggered the alert")
    structured_data: Dict[str, Any] = Field(description="The structured JSON response as requested by the alert requester")
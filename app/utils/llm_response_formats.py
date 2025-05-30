from pydantic import BaseModel, Field

class LLMValidationFormat(BaseModel):
    
    approval: bool = Field(description="Is the alert's request valid?")
    chance_score: float = Field(ge=0.0, le=1.0, description="Estimation of the quality of the request. Ranging from 0.0 to 1.0. Must be at least 0.85 to approve.")
    reason: str = Field(description="Reason for the approval or denial")
    keywords: list[str] = Field(description="The keywords that MUST be in the data that triggers the alert")


class LLMVerificationFormat(BaseModel):
    
    approval: bool = Field(description="Whether the document matches the alert's intent")
    chance_score: float = Field(ge=0.0, le=1.0, description="Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.")
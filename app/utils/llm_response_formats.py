from pydantic import BaseModel, Field

class LLMValidationFormat(BaseModel):
    
    approval: bool = Field(default=False, description="Whether the alert's request is a valid one")
    chance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.")
    
    def __init__(self, approval: bool, chance_score: float):
        self.approval = approval
        self.chance_score = chance_score


class LLMVerificationFormat(BaseModel):
    
    approval: bool = Field(default=False, description="Whether the document matches the alert's intent")
    chance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Validation estimate ranging from 0.0 to 1.0. Must be at least 0.85 to approve.")
    
    def __init__(self, approval: bool, chance_score: float):
        self.approval = approval
        self.chance_score = chance_score
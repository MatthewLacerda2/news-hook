from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class UserDocumentCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, description="The name of the document")
    content: str = Field(..., min_length=10, description="The actual content of the document")
    should_save: Optional[bool] = Field(True, description="Should we save the document?")  #TODO: implement

class UserDocumentCreateSuccessResponse(BaseModel):
    id: str = Field(..., description="The id of the document")
    name: str = Field(..., description="The name of the document")
    created_at: datetime = Field(..., description="The date and time the document was created")

class UserDocumentItem(BaseModel):
    id: str = Field(..., description="The id of the document")
    name: str = Field(..., description="The name of the document")
    #Gemini-embedding-exp-03-07 has a 2048 token limit
    content: str = Field(..., lte = 2048 * 4, description="The content of the document itself. Limit of 2048 tokens.")
    uploaded_at: datetime = Field(..., description="The date and time the document was uploaded by the user")

    model_config = ConfigDict(from_attributes=True)
    
class UserDocumentListResponse(BaseModel):
    documents: list[UserDocumentItem]
    total_count: int
    
    model_config = ConfigDict(from_attributes=True)
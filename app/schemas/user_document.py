from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
class UserDocumentCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, description="The name of the document")
    content: str = Field(..., min_length=10, description="The actual content of the document")

class UserDocumentCreateSuccessResponse(BaseModel):
    id: str = Field(..., description="The id of the document")
    name: str = Field(..., description="The name of the document")
    created_at: datetime = Field(..., description="The date and time the document was created")

class UserDocumentItem(BaseModel):
    id: str = Field(..., description="The id of the document")
    name: str = Field(..., description="The name of the document")
    content: str = Field(..., description="The content of the document itself")
    uploaded_at: datetime = Field(..., description="The date and time the document was uploaded by the user")

    model_config = ConfigDict(from_attributes=True)
from pydantic import BaseModel, Field
from datetime import datetime
class UserDocumentCreateRequest(BaseModel):
    name: str = Field(..., description="The name of the document")
    content: str = Field(..., description="The actual content of the document")

class UserDocumentCreateSuccessResponse(BaseModel):
    id: str = Field(..., description="The id of the document")
    name: str = Field(..., description="The name of the document")
    created_at: datetime = Field(..., description="The date and time the document was created")


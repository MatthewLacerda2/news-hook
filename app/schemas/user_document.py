from pydantic import BaseModel, Field

class UserDocument(BaseModel):
    name: str = Field(..., description="The name of the document")
    content: str = Field(..., description="The actual content of the document")

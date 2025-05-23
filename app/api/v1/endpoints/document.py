from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.schemas.user_document import UserDocumentCreateRequest, UserDocumentCreateResponse
from app.core.database import get_db
from app.models.agent_controller import AgentController
from app.core.security import get_user_by_api_key
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_document import UserDocument
from app.tasks.llm_apis.ollama import get_nomic_embeddings
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=UserDocumentCreateResponse, status_code=status.HTTP_201_CREATED)
async def post_document(
    user_document: UserDocumentCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key),
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    """
    Create a new document
    """
    
    #TODO: do like create_alert and have this delegated to someone else
    if user.id != x_user_id:
        raise HTTPException(status_code=403, detail="Not authenticated: user_id and api_key mismatch")
    
    # Validate name and content length
    if len(user_document.name) < 3:
        raise HTTPException(status_code=401, detail="name must be at least 3 characters long")
    if len(user_document.content) < 16:
        raise HTTPException(status_code=401, detail="content must be at least 16 characters long")

    try:
        embedding = await get_nomic_embeddings(user_document.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

    new_doc = UserDocument(
        id=str(uuid.uuid4()),
        agent_controller_id=user.id,
        name=user_document.name,
        uploaded_datetime=datetime.now(),
        content=user_document.content,
        content_embedding=embedding
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    #TODO: async task to verify for alerts

    return UserDocumentCreateResponse(
        id=new_doc.id,
        name=new_doc.name,
        created_at=new_doc.uploaded_datetime
    )


#async def get_document(
#    document_id: str,
#)

#async def list_documents(
#    agent_controller_id: str,
#)

#async def delete_document(
#    document_id: str,
#)

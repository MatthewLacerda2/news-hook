from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_document import UserDocumentCreateRequest, UserDocumentCreateSuccessResponse
from app.tasks.save_embedding import generate_and_save_document_embeddings
from app.tasks.vector_search import perform_embed_and_vector_search
from app.utils.sourced_data import SourcedData, DataSource
from app.models.agent_controller import AgentController
from app.core.security import get_user_by_api_key
from app.models.user_document import UserDocument
from app.core.database import get_db
from datetime import datetime
from app.utils.env import NUM_EMBEDDING_DIMENSIONS
import numpy as np
import asyncio
import uuid
router = APIRouter()

async def process_user_document(user_document: UserDocument):
    await generate_and_save_document_embeddings(
        user_document.id,
        user_document.content
    )
    
    sourced_data = SourcedData(
        agent_controller_id=user_document.agent_controller_id,
        source=DataSource.USER_DOCUMENT,
        source_url=user_document.id,
        source_id=user_document.id,
        document_id=user_document.id,
        name=user_document.name,
        content=user_document.content,
        content_embedding=np.zeros(NUM_EMBEDDING_DIMENSIONS)
    )
    
    await perform_embed_and_vector_search(
        sourced_data
    )

@router.post("/", response_model=UserDocumentCreateSuccessResponse, status_code=status.HTTP_201_CREATED)
async def post_document(
    user_document: UserDocumentCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key),
):
    """
    Create a new document
    """

    new_doc = UserDocument(
        id=str(uuid.uuid4()),
        agent_controller_id=user.id,
        name=user_document.name,
        content=user_document.content,
        content_embedding=None,
        uploaded_datetime=datetime.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    asyncio.create_task(
        process_user_document(new_doc)
    )

    return UserDocumentCreateSuccessResponse(
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

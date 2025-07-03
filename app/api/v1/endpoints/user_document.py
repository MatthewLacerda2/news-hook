from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func, cast
from app.schemas.user_document import UserDocumentCreateRequest, UserDocumentCreateSuccessResponse, UserDocumentItem, UserDocumentListResponse
from app.tasks.save_embedding import generate_and_save_document_embeddings
from app.tasks.vector_search import vector_search
from app.utils.sourced_data import SourcedData
from app.models.agent_controller import AgentController
from app.core.security import get_user_by_api_key
from app.core.database import get_db
from datetime import datetime
from app.models.monitored_data import MonitoredData, DataSource
from app.utils.env import NUM_EMBEDDING_DIMENSIONS
import numpy as np
import asyncio
import uuid
from typing import Optional
from sqlalchemy.types import String
from app.tasks.chat.vector_search_chat import vector_search_chat

router = APIRouter()

async def process_document(document: MonitoredData):
    await generate_and_save_document_embeddings(
        document.id,
        document.content
    )
    
    sourced_data = SourcedData(
        id=document.id,
        source=document.source,
        content=document.content,
        content_embedding=np.zeros(NUM_EMBEDDING_DIMENSIONS),
        name=document.name,
        agent_controller_id=document.agent_controller_id,
        document_id=document.id
    )
    
    await vector_search(
        sourced_data
    )
    if document.source != DataSource.USER_DOCUMENT:
        await vector_search_chat(
            sourced_data
        )

@router.post(
    "/",
    response_model=UserDocumentCreateSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new document"
)
async def post_user_document(
    user_document: UserDocumentCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key),
):

    new_doc = MonitoredData(
        id=str(uuid.uuid4()),
        agent_controller_id=user.id,
        source=DataSource.USER_DOCUMENT,
        name=user_document.name,
        content=user_document.content,
        content_embedding=None,
        monitored_datetime=datetime.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    asyncio.create_task(
        process_document(new_doc)
    )

    return UserDocumentCreateSuccessResponse(
        id=new_doc.id,
        name=new_doc.name,
        created_at=new_doc.monitored_datetime
    )

@router.post(
    "/manual",
    response_model=UserDocumentCreateSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    description="Admin documents"
)
async def post_admin_document(
    user_document: UserDocumentCreateRequest,
    db: AsyncSession = Depends(get_db),
    agent_controller: AgentController = Depends(get_user_by_api_key),
):
    
    if agent_controller.email != "matheus.l1996@gmail.com": #TODO: change to check by IAM token.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authorized users can create documents"
        )
        
    new_doc = MonitoredData(
        id=str(uuid.uuid4()),
        agent_controller_id=agent_controller.id,
        source=DataSource.MANUAL_DOCUMENT,
        name=user_document.name,
        content=user_document.content,
        content_embedding=None,
        monitored_datetime=datetime.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    asyncio.create_task(
        process_document(new_doc)
    )
    
    return UserDocumentCreateSuccessResponse(
        id=new_doc.id,
        name=new_doc.name,
        created_at=new_doc.monitored_datetime
    )

@router.get(
    "/{document_id}",
    response_model=UserDocumentItem,
    description="Get a document by ID"
)
async def get_user_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key),
):
    
    query = select(MonitoredData).where(
        MonitoredData.id == document_id,
        MonitoredData.agent_controller_id == user.id
    )
    
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    
    return UserDocumentItem(
        id=document.id,
        name=document.name,
        content=document.content,
        uploaded_at=document.monitored_datetime
    )
   
@router.get(
    "/",
    response_model=UserDocumentListResponse,
    description="List all documents for the authenticated user. Can filter by substrings in the name or content."
)
async def get_user_documents(
    contains: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key),
):
    # Base query
    base_filter = (MonitoredData.agent_controller_id == user.id)
    
    # Add contains filter if provided
    if contains:
        contains_filter = or_(
            MonitoredData.name.ilike(f"%{contains}%"),
            cast(MonitoredData.content, String).ilike(f"%{contains}%")  # Cast JSON to string before ILIKE
        )
        base_filter = and_(base_filter, contains_filter)
    
    # Get total count
    count_stmt = select(func.count()).select_from(MonitoredData).where(base_filter)
    total_count = await db.execute(count_stmt)
    total_count = total_count.scalar()
    
    # Get paginated results
    stmt = select(MonitoredData).where(base_filter).offset(offset).limit(limit)
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    return UserDocumentListResponse(
        documents=[
            UserDocumentItem(
                id=doc.id,
                name=doc.name,
                content=doc.content,
                uploaded_at=doc.monitored_datetime
            )
            for doc in documents
        ],
        total_count=total_count
    )
    
@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a document by ID"
)
async def delete_user_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key),
):
    query = select(MonitoredData).where(
        MonitoredData.id == document_id,
        MonitoredData.agent_controller_id == user.id
    )
    
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    
    await db.delete(document)
    await db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get(
    "/public",
    response_model=UserDocumentListResponse,
    description="List public documents"
)
async def get_public_documents(
    contains: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    # Base query - filter for documents that are not user documents
    base_filter = (MonitoredData.source != DataSource.USER_DOCUMENT)
    
    # Add contains filter if provided
    if contains:
        contains_filter = or_(
            MonitoredData.name.ilike(f"%{contains}%"),
            cast(MonitoredData.content, String).ilike(f"%{contains}%")  # Cast JSON to string before ILIKE
        )
        base_filter = and_(base_filter, contains_filter)
    
    # Get total count
    count_stmt = select(func.count()).select_from(MonitoredData).where(base_filter)
    total_count = await db.execute(count_stmt)
    total_count = total_count.scalar()
    
    # Get paginated results
    stmt = select(MonitoredData).where(base_filter).offset(offset).limit(limit)
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    return UserDocumentListResponse(
        documents=[
            UserDocumentItem(
                id=doc.id,
                name=doc.name,
                content=doc.content,
                uploaded_at=doc.monitored_datetime
            )
            for doc in documents
        ],
        total_count=total_count
    )
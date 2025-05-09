from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
import asyncio

from app.core.database import get_db
from app.models.agent_controller import AgentController
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.schemas.alert_prompt import (
    AlertPromptCreateRequestBase,
    AlertPromptCreateSuccessResponse,
    AlertPromptListResponse,
    AlertPromptItem
)
from app.core.security import get_user_by_api_key
from app.models.llm_models import LLMModel
from app.utils.llm_validator import get_llm_validation, get_llm_validation_price
from app.utils.count_tokens import count_tokens
from app.models.llm_validation import LLMValidation
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func
from app.tasks.save_embedding import generate_and_save_embeddings
from app.utils.env import MAX_DATETIME, LLM_APPROVAL_THRESHOLD
from app.schemas.alert_prompt import AlertCancelRequest
from app.models.notification import Notification
from app.schemas.notification import NotificationCreateRequestBase, NotificationCreateSuccessResponse, NotificationListResponse, NotificationItem

import uuid

router = APIRouter()

@router.post("/", response_model=NotificationCreateSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreateRequestBase,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Create a new notification"""

    if user.credit_balance <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient credits"
        )
    
    try:
        now = datetime.now()
        
        stmt = select(LLMModel).where(
            LLMModel.model_name == notification_data.llm_model,
            LLMModel.is_active == True
        )
        result = await db.execute(stmt)
        llm_model = result.scalar_one_or_none()
        if not llm_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid LLM model"
            )

        #TODO: switch from 'validation' for notification specific prompt
        llm_validation_response = await get_llm_validation(notification_data, llm_model.model_name)

        if not llm_validation_response.approval or llm_validation_response.chance_score < LLM_APPROVAL_THRESHOLD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid alert request"
            )
        
        input_price, output_price = get_llm_validation_price(notification_data, llm_validation_response, llm_model)
        tokens_price = input_price + output_price
        
        if user.credit_balance < tokens_price:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient credits"
            )
            
        new_notification = Notification(
            id=str(uuid.uuid4()),
            agent_controller_id=user.id,
            prompt=notification_data.prompt,
            http_method=notification_data.http_method,
            http_url=str(notification_data.http_url),
            http_headers=notification_data.http_headers or {},
            payload_format=notification_data.payload_format or {},
            keywords=llm_validation_response.keywords,
            expires_at=notification_data.max_datetime or (now + timedelta(days=MAX_DATETIME)),
            llm_model=notification_data.llm_model
        )

        llm_validation = LLMValidation(
            id=str(uuid.uuid4()),
            prompt_id=new_notification.id,
            approval=llm_validation_response.approval,
            chance_score=llm_validation_response.chance_score,
            input_tokens=count_tokens(notification_data.prompt, llm_model.model_name),
            input_price=input_price,
            output_tokens=count_tokens(llm_validation_response.output_intent, llm_model.model_name),
            output_price=output_price,
            llm_id=llm_model.id,
            date_time=now
        )
        user.credit_balance -= tokens_price
        db.add(llm_validation)
        db.add(new_notification)
        
        await db.commit()
        await db.refresh(new_notification)
        
        asyncio.create_task(
            generate_and_save_embeddings(
                new_notification.id,
                notification_data.prompt,
            )
        )
        
        return AlertPromptCreateSuccessResponse(
            id=new_notification.id,
            prompt=new_notification.prompt,
            created_at=new_notification.created_at,
            output_intent=llm_validation_response.output_intent,
            keywords=llm_validation_response.keywords
        )
        
    except HTTPException as e:
        raise e  # re-raise HTTPExceptions so FastAPI can handle them
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating alert: {str(e)}"
        )

@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    prompt_contains: Optional[str] = None,
    max_datetime: Optional[datetime] = None,
    created_after: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """List notifications for the authenticated user with filtering and pagination"""
    
    if created_after and max_datetime and created_after > max_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="created_after cannot be later than max_datetime"
        )
    
    stmt = select(Notification).where(Notification.agent_controller_id == user.id)
    count_stmt = select(func.count()).select_from(Notification).where(Notification.agent_controller_id == user.id)

    if prompt_contains:
        stmt = stmt.filter(Notification.prompt.ilike(f"%{prompt_contains}%"))
        count_stmt = count_stmt.filter(Notification.prompt.ilike(f"%{prompt_contains}%"))
    if max_datetime:
        stmt = stmt.filter(Notification.expires_at <= max_datetime)
        count_stmt = count_stmt.filter(Notification.expires_at <= max_datetime)
    if created_after:
        stmt = stmt.filter(Notification.created_at >= created_after)
        count_stmt = count_stmt.filter(Notification.created_at >= created_after)

    alerts = await db.execute(stmt.offset(offset).limit(limit))
    
    total_count = await db.execute(count_stmt)
    total_count = total_count.scalar()
    
    return AlertPromptListResponse(
        alerts=[
            AlertPromptItem.model_validate(alert) for alert in alerts.scalars().all()
        ],
        total_count=total_count
    )

@router.get("/{notification_id}", response_model=NotificationItem)
async def get_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Get a specific alert by ID"""
    
    # Find the alert and verify ownership
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.agent_controller_id == user.id
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    return notification_to_schema(notification)

def notification_to_schema(notification: Notification) -> NotificationItem:
    return NotificationItem(
        id=notification.id,
        prompt=notification.prompt,
        http_method=notification.http_method,
        http_url=notification.http_url,
        http_headers=notification.http_headers or {},
        payload_format=notification.payload_format or {},
        tags=notification.keywords,
        status=notification.status,
        created_at=notification.created_at,
        expires_at=notification.expires_at,
        llm_model=notification.llm_model
    )

#Alert can not be 'deleted'. They costed credits and thus have to be kept register of.
@router.patch("/{notification_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Cancel an existing notification"""
    
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.agent_controller_id == user.id
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    notification.status = AlertStatus.CANCELLED
    await db.commit()
    
    return {"message": "Notification cancelled successfully"}

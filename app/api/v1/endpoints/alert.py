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
    AlertPromptItem,
    AlertPatchRequest
)
from app.core.security import get_user_by_api_key
from app.models.llm_models import LLMModel
from app.utils.llm_validator import get_llm_validation, get_token_price, is_alert_duplicated
from app.utils.count_tokens import count_tokens
from app.models.llm_validation import LLMValidation
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func
from app.tasks.save_embedding import generate_and_save_alert_embeddings
import uuid
from app.utils.env import MAX_DATETIME, LLM_VALIDATION_THRESHOLD, ALERT_CREATION_PRICE, FLAGSHIP_MODEL
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=AlertPromptCreateSuccessResponse,
    description="Create a new alert for monitoring"
)
async def create_alert(
    alert_data: AlertPromptCreateRequestBase,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    
    try:
        
        if alert_data.llm_model is None:
            alert_data.llm_model = FLAGSHIP_MODEL
                
        stmt = select(LLMModel).where(
            LLMModel.model_name == alert_data.llm_model,
            LLMModel.is_active == True
        )
        result = await db.execute(stmt)
        llm_model = result.scalar_one_or_none()
        if not llm_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid LLM model"
            )

        is_duplicated = await is_alert_duplicated(alert_data, user.id, db)  #TODO: test
        if is_duplicated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert already exists"
            )

        llm_validation_response = get_llm_validation(alert_data.prompt)
        llm_validation_str = llm_validation_response.model_dump_json()
                
        input_price, output_price = get_token_price(alert_data.prompt, llm_validation_str, llm_model)
        
        tokens_price = input_price + output_price
            
        now = datetime.now()
            
        llm_validation = LLMValidation(
            id=str(uuid.uuid4()),
            prompt_id=None,
            prompt=alert_data.prompt[:255],
            reason=llm_validation_response.reason[:128],
            approval=llm_validation_response.approval,
            chance_score=llm_validation_response.chance_score,
            input_tokens=count_tokens(alert_data.prompt, llm_model.model_name),
            input_price=input_price,
            output_tokens=count_tokens(llm_validation_response.reason, llm_model.model_name),
            output_price=output_price,
            llm_model=llm_model.model_name,
            date_time=now
        )
        db.add(llm_validation)
        await db.commit()

        if not llm_validation_response.approval or llm_validation_response.chance_score < LLM_VALIDATION_THRESHOLD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "approval": llm_validation_response.approval,
                    "chance_score": llm_validation_response.chance_score,
                    "reason": llm_validation_response.reason,
                    "keywords": llm_validation_response.keywords
                }
            )
        
        new_alert = AlertPrompt(
            id=str(uuid.uuid4()),
            agent_controller_id=user.id,
            prompt=alert_data.prompt,
            http_method=alert_data.http_method,
            http_url=str(alert_data.http_url),
            http_headers=alert_data.http_headers or None,
            is_recurring=alert_data.is_recurring,
            keywords=llm_validation_response.keywords,
            expires_at=alert_data.max_datetime.replace(tzinfo=None) if alert_data.max_datetime else (now + timedelta(days=MAX_DATETIME)),
            llm_model=alert_data.llm_model
        )
        
        llm_validation.prompt_id = new_alert.id
        db.add(new_alert)
        
        user.credit_balance -= tokens_price
        user.credit_balance -= ALERT_CREATION_PRICE
        await db.commit()
        await db.refresh(new_alert)
        
        asyncio.create_task(
            generate_and_save_alert_embeddings(
                new_alert.id,
                alert_data.prompt,
            )
        )
        
        return AlertPromptCreateSuccessResponse(
            id=new_alert.id,
            prompt=new_alert.prompt,
            created_at=new_alert.created_at,
            reason=llm_validation_response.reason,
            keywords=llm_validation_response.keywords
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating alert: {str(e)}"
        )

@router.get(
    "/",
    response_model=AlertPromptListResponse,
    description="List all alerts for the authenticated user with filtering and pagination"
)
async def list_alerts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    prompt_contains: Optional[str] = None,
    max_datetime: Optional[datetime] = None,
    created_after: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    
    if created_after and max_datetime and created_after > max_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="created_after cannot be later than max_datetime"
        )
    
    stmt = select(AlertPrompt).where(AlertPrompt.agent_controller_id == user.id)
    count_stmt = select(func.count()).select_from(AlertPrompt).where(AlertPrompt.agent_controller_id == user.id)

    if prompt_contains:
        stmt = stmt.filter(AlertPrompt.prompt.ilike(f"%{prompt_contains}%"))
        count_stmt = count_stmt.filter(AlertPrompt.prompt.ilike(f"%{prompt_contains}%"))
    if max_datetime:
        stmt = stmt.filter(AlertPrompt.expires_at <= max_datetime)
        count_stmt = count_stmt.filter(AlertPrompt.expires_at <= max_datetime)
    if created_after:
        stmt = stmt.filter(AlertPrompt.created_at >= created_after)
        count_stmt = count_stmt.filter(AlertPrompt.created_at >= created_after)

    # Add ordering by created_at
    stmt = stmt.order_by(AlertPrompt.created_at.desc())

    alerts = await db.execute(stmt.offset(offset).limit(limit))
    
    total_count = await db.execute(count_stmt)
    total_count = total_count.scalar()
    
    return AlertPromptListResponse(
        alerts=[
            AlertPromptItem.model_validate(alert) for alert in alerts.scalars().all()
        ],
        total_count=total_count
    )

@router.get(
    "/{alert_id}",
    response_model=AlertPromptItem,
    description="Get a specific alert by ID"
)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    
    stmt = select(AlertPrompt).where(
        AlertPrompt.id == alert_id,
        AlertPrompt.agent_controller_id == user.id
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    return alert_to_schema(alert)

def alert_to_schema(alert: AlertPrompt) -> AlertPromptItem:
    return AlertPromptItem(
        id=alert.id,
        prompt=alert.prompt,
        http_method=alert.http_method,
        http_url=alert.http_url,
        http_headers=alert.http_headers or None,
        tags=alert.keywords,
        status=alert.status,
        created_at=alert.created_at,
        expires_at=alert.expires_at,
        llm_model=alert.llm_model,
        is_recurring=alert.is_recurring
    )

@router.patch(
    "/{alert_id}/cancel",
    status_code=status.HTTP_200_OK,
    description="Mark an alert as CANCELLED. We do not 'delete' the alert, for billing purposes")
async def cancel_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    
    stmt = select(AlertPrompt).where(
        AlertPrompt.id == alert_id,
        AlertPrompt.agent_controller_id == user.id
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    alert.status = AlertStatus.CANCELLED
    await db.commit()
    
    return {"message": "Alert cancelled successfully"}

@router.patch(
    "/{alert_id}",
    status_code=status.HTTP_200_OK,
    response_model=AlertPromptItem,
    description="Patch an alert"
)
async def patch_alert(
    alert_id: str,
    alert_data: AlertPatchRequest,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    
    stmt = select(AlertPrompt).where(
        AlertPrompt.id == alert_id,
        AlertPrompt.agent_controller_id == user.id
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    if alert.status != AlertStatus.ACTIVE and alert.status != AlertStatus.WARNED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is not active"
        )
    
    if alert_data.http_url:
        alert.http_url = str(alert_data.http_url)
    if alert_data.http_headers:
        alert.http_headers = alert_data.http_headers
    if alert_data.is_recurring:
        alert.is_recurring = alert_data.is_recurring
    if alert_data.http_method:
        alert.http_method = alert_data.http_method
    if alert_data.llm_model:
        alert.llm_model = alert_data.llm_model
    if alert_data.max_datetime:
        alert.expires_at = alert_data.max_datetime.replace(tzinfo=None) if alert_data.max_datetime else (datetime.now() + timedelta(days=MAX_DATETIME))
        
    await db.commit()
    
    return alert_to_schema(alert)
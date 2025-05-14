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
import uuid

router = APIRouter()

@router.post("/", response_model=AlertPromptCreateSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertPromptCreateRequestBase,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Create a new alert for monitoring"""
    
    print(alert_data.model_dump_json())

    if user.credit_balance <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient credits"
        )
    
    try:
        now = datetime.now()
        
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

        new_alert_id = str(uuid.uuid4())
        llm_validation_response = await get_llm_validation(alert_data, llm_model.model_name)
        llm_validation = LLMValidation(
            id=str(uuid.uuid4()),
            prompt_id=new_alert_id,
            approval=llm_validation_response.approval,
            chance_score=llm_validation_response.chance_score,
            input_tokens=count_tokens(alert_data.prompt, llm_model.model_name),
            input_price=input_price,
            output_tokens=count_tokens(llm_validation_response.output_intent, llm_model.model_name),
            output_price=output_price,
            llm_id=llm_model.id,
            date_time=now
        )
        db.add(llm_validation)

        if not llm_validation_response.approval or llm_validation_response.chance_score < 0.85:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid alert request",
                    "validation": {
                        "approval": llm_validation_response.approval,
                        "chance_score": llm_validation_response.chance_score,
                        "output_intent": llm_validation_response.output_intent,
                        "keywords": llm_validation_response.keywords
                    }
                }
            )
        
        input_price, output_price = get_llm_validation_price(alert_data, llm_validation_response, llm_model)
        tokens_price = input_price + output_price
        
        if user.credit_balance < tokens_price:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient credits"
            )
            
        new_alert = AlertPrompt(
            id=new_alert_id,
            agent_controller_id=user.id,
            prompt=alert_data.prompt,
            http_method=alert_data.http_method,
            http_url=str(alert_data.http_url),
            http_headers=alert_data.http_headers or {},
            payload_format=alert_data.payload_format or {},
            is_recurring=alert_data.is_recurring,
            keywords=llm_validation_response.keywords,
            expires_at=alert_data.max_datetime or (now + timedelta(days=300)),
            llm_model=alert_data.llm_model
        )

        user.credit_balance -= tokens_price
        db.add(new_alert)
        
        await db.commit()
        await db.refresh(new_alert)
        
        asyncio.create_task(
            generate_and_save_embeddings(
                new_alert.id,
                alert_data.prompt,
            )
        )
        
        return AlertPromptCreateSuccessResponse(
            id=new_alert.id,
            prompt=new_alert.prompt,
            created_at=new_alert.created_at,
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

@router.get("/", response_model=AlertPromptListResponse)
async def list_alerts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    prompt_contains: Optional[str] = None,
    max_datetime: Optional[datetime] = None,
    created_after: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """List alerts for the authenticated user with filtering and pagination"""
    
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

    alerts = await db.execute(stmt.offset(offset).limit(limit))
    
    total_count = await db.execute(count_stmt)
    total_count = total_count.scalar()
    
    return AlertPromptListResponse(
        alerts=[
            AlertPromptItem.model_validate(alert) for alert in alerts.scalars().all()
        ],
        total_count=total_count
    )

@router.get("/{alert_id}", response_model=AlertPromptItem)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Get a specific alert by ID"""
    
    # Find the alert and verify ownership
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
        http_headers=alert.http_headers or {},
        payload_format=alert.payload_format or {},
        tags=alert.keywords,
        status=alert.status,
        created_at=alert.created_at,
        expires_at=alert.expires_at,
        llm_model=alert.llm_model
    )

#Alert can not be 'deleted'. They costed credits and thus have to be kept register of.
@router.patch("/{alert_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Cancel an existing alert"""
    
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

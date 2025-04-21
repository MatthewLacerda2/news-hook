from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

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
from app.utils.llm_validator import llm_validation
from app.tasks.llm_apis.ollama import get_nomic_embeddings

router = APIRouter()

@router.post("/", response_model=AlertPromptCreateSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertPromptCreateRequestBase,
    db: Session = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Create a new alert for monitoring"""

    if user.credit_balance <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient credits"
        )
    
    try:
        now = datetime.now()
        
        llm_model = db.query(LLMModel).filter(
            LLMModel.model_name == alert_data.llm_model,
            LLMModel.is_active == True
        ).first()
        if not llm_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"LLM model '{alert_data.llm_model}' not found"
            )

        llm_validation_response = llm_validation(alert_data, llm_model)

        if not llm_validation_response.approval or llm_validation_response.chance_score < 0.85:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid alert request"
            )
        
        # Create new alert
        new_alert = AlertPrompt(
            user_id=user.id,
            prompt=alert_data.prompt,
            prompt_embedding = get_nomic_embeddings(alert_data.prompt),
            http_method=alert_data.http_method,
            http_url=str(alert_data.http_url),
            parsed_intent=alert_data.parsed_intent or {},
            parsed_intent_embedding = get_nomic_embeddings(str(alert_data.parsed_intent)),
            example_response=alert_data.example_response or {},
            max_datetime=alert_data.max_datetime or (now + timedelta(days=300)),
            llm_model=alert_data.llm_model,
            keywords=llm_validation_response.keywords,
            status=AlertStatus.ACTIVE
        )
        
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        
        return AlertPromptCreateSuccessResponse(
            id=new_alert.id,
            prompt=new_alert.prompt,
            created_at=new_alert.created_at,
            output_intent=llm_validation_response.output_intent,
            keywords=llm_validation_response.keywords
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating alert: {str(e)}"
        )

#check alert price

@router.get("/", response_model=AlertPromptListResponse)
async def list_alerts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    prompt_contains: Optional[str] = None,
    max_datetime: Optional[datetime] = None,
    created_after: Optional[datetime] = None,
    db: Session = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """List alerts for the authenticated user with filtering and pagination"""
    
    # Validate created_after against max_datetime if both are provided
    if created_after and max_datetime and created_after > max_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="created_after cannot be later than max_datetime"
        )
    
    # Build the query
    query = db.query(AlertPrompt).filter(AlertPrompt.agent_controller_id == user.id)
    
    # Apply filters if provided
    if prompt_contains:
        query = query.filter(AlertPrompt.prompt.ilike(f"%{prompt_contains}%"))
    if max_datetime:
        query = query.filter(AlertPrompt.expires_at <= max_datetime)
    if created_after:
        query = query.filter(AlertPrompt.created_at >= created_after)
    
    # Apply pagination
    total = query.count()
    alerts = query.offset(offset).limit(limit).all()
    
    return AlertPromptListResponse(
        alerts=[
            AlertPromptItem.model_validate(alert) for alert in alerts
        ],
        total=total
    )

#cancel alert (they cannot be 'deleted' because creating them costed credits, thus we must keep track)

@router.patch("/{alert_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Cancel an existing alert"""
    
    # Find the alert and verify ownership
    alert = db.query(AlertPrompt).filter(
        AlertPrompt.id == alert_id,
        AlertPrompt.agent_controller_id == user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    # Update alert status to cancelled
    alert.status = AlertStatus.CANCELLED
    db.commit()
    
    return {"message": "Alert cancelled successfully"}
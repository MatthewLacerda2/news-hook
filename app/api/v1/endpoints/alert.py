from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.models.agent_controller import AgentController
from app.models.alert_prompt import AlertPrompt, AlertStatus, HttpMethod
from app.schemas.alert_prompt import (
    AlertPromptCreateRequestBase,
    AlertPromptCreateSuccessResponse
)
from app.core.security import get_user_by_api_key

router = APIRouter()

@router.post("/", response_model=AlertPromptCreateSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertPromptCreateRequestBase,
    db: Session = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    """Create a new alert for monitoring"""
    
    # Check if user has sufficient credits
    if user.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient credits"
        )
    
    try:
        now = datetime.utcnow()
        # Create new alert
        new_alert = AlertPrompt(
            user_id=user.id,
            prompt=alert_data.prompt,
            http_method=alert_data.http_method,
            http_url=str(alert_data.http_url),
            parsed_intent=alert_data.parsed_intent or {},
            example_response=alert_data.example_response or {},
            max_datetime=alert_data.max_datetime or (now + timedelta(days=300)),
            keywords=[],  # Will be populated by LLM processing
            status=AlertStatus.ACTIVE
        )
        
        # TODO: Process prompt with LLM to extract keywords and generate output_intent
        output_intent = "Placeholder output intent"
        keywords = []
        
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        
        return AlertPromptCreateSuccessResponse(
            id=new_alert.id,
            prompt=new_alert.prompt,
            output_intent=output_intent,
            created_at=new_alert.created_at,
            keywords=keywords
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating alert: {str(e)}"
        )

#check alert price

#get user' alerts

#cancel alert (they cannot be 'deleted' because creating them costed credits, thus we must keep track)
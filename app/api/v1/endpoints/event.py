from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from app.core.security import get_user_by_api_key
from app.core.config import settings
from app.core.security import create_access_token, verify_google_token, verify_token, get_current_user
from app.core.database import get_db
from app.schemas.agent_controller import OAuth2Request, TokenResponse
from app.models.agent_controller import AgentController

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import uuid
from typing import Optional
from sqlalchemy.sql import func
from app.schemas.alert_event import AlertEventListResponse, AlertEventItem
from app.models.alert_prompt import AlertPrompt
from app.models.alert_event import AlertEvent


router = APIRouter()

@router.get(
    "/",
    response_model=AlertEventListResponse,
    description="List all events for the authenticated user with filtering and pagination"
)
async def list_events(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    triggered_before: Optional[datetime] = None,
    triggered_after: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    user: AgentController = Depends(get_user_by_api_key)
):
    if triggered_before and triggered_after and triggered_before < triggered_after:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="triggered_after cannot be later than triggered_before"
        )
    
    stmt = (
        select(AlertEvent, AlertPrompt.prompt, AlertPrompt.http_method, 
               AlertPrompt.http_url, AlertPrompt.is_recurring)
        .join(AlertPrompt, AlertEvent.alert_prompt_id == AlertPrompt.id)
        .where(AlertPrompt.agent_controller_id == user.id)
    )
    
    count_stmt = (
        select(func.count())
        .select_from(AlertEvent)
        .join(AlertPrompt, AlertEvent.alert_prompt_id == AlertPrompt.id)
        .where(AlertPrompt.agent_controller_id == user.id)
    )
    
    if triggered_before:
        stmt = stmt.filter(AlertEvent.triggered_at <= triggered_before)
        count_stmt = count_stmt.filter(AlertEvent.triggered_at <= triggered_before)
    if triggered_after:
        stmt = stmt.filter(AlertEvent.triggered_at >= triggered_after)
        count_stmt = count_stmt.filter(AlertEvent.triggered_at >= triggered_after)

    stmt = stmt.order_by(AlertEvent.triggered_at.desc())

    events = await db.execute(stmt.offset(offset).limit(limit))
    
    total_count = await db.execute(count_stmt)
    total_count = total_count.scalar()
    
    event_items = []
    for event_tuple in events:
        event, prompt, http_method, http_url, is_recurring = event_tuple
        event_dict = {
            "id": event.id,
            "alert_prompt_id": event.alert_prompt_id,
            "triggered_at": event.triggered_at,
            "structured_data": event.structured_data,
            "prompt": prompt,
            "http_method": http_method,
            "http_url": http_url,
            "is_recurring": is_recurring
        }
        event_items.append(AlertEventItem.model_validate(event_dict))
    
    return AlertEventListResponse(
        events=event_items,
        total_count=total_count
    )

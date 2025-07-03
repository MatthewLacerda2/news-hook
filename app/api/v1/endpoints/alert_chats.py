import logging
from fastapi import APIRouter
from fastapi import status
from app.utils.llm_validator import is_alert_chat_duplicated, get_llm_validation
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.utils.env import LLM_VERIFICATION_THRESHOLD, FLAGSHIP_MODEL
from app.utils.llm_validator import get_token_price
from app.models.llm_models import LLMModel
from app.models.llm_validation import LLMValidation
from app.utils.llm_validator import count_tokens
from app.models.alert_chat import AlertChat, AlertChatStatus
from datetime import datetime, timedelta
import uuid
import asyncio
from app.tasks.save_embedding import generate_and_save_alert_chat_embeddings
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()
#TODO: tests for them' all

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=str,
    description="Create a new alert for monitoring"
)
async def create_alert_chat(prompt: str, telegram_id: str, db: AsyncSession = Depends(get_db)):
    
    is_duplicated = await is_alert_chat_duplicated(prompt, telegram_id, db)
    if is_duplicated:
        return "That Alert is already active"
    
    stmt = select(LLMModel).where(
        LLMModel.model_name == FLAGSHIP_MODEL
    )
    result = await db.execute(stmt)
    llm_model = result.scalar_one_or_none()
    
    llm_validation_response = get_llm_validation(prompt, llm_model.model_name)
    llm_validation_str = llm_validation_response.model_dump_json()
                
    input_price, output_price = get_token_price(prompt, llm_validation_str, llm_model)
        
    now = datetime.now()
        
    llm_validation = LLMValidation(
        id=str(uuid.uuid4()),
        prompt_id=None,
        alert_chat_id=None,
        prompt=prompt[:255],
        reason=llm_validation_response.reason[:128],
        approval=llm_validation_response.approval,
        chance_score=llm_validation_response.chance_score,
        input_tokens=count_tokens(prompt, FLAGSHIP_MODEL),
        input_price=input_price,
        output_tokens=count_tokens(llm_validation_response.reason, FLAGSHIP_MODEL),
        output_price=output_price,
        llm_model=FLAGSHIP_MODEL,
        date_time=now
    )
    db.add(llm_validation)
    await db.commit()

    if not llm_validation_response.approval or llm_validation_response.chance_score < LLM_VERIFICATION_THRESHOLD:
        return "I'm sorry, I cannot create an alert on that. Reason: " + llm_validation_response.reason
    
    expire_date = (now + timedelta(days=30)).replace(hour=23, minute=59, second=59)
    
    new_alert_chat = AlertChat(
        id=str(uuid.uuid4()),
        telegram_id=telegram_id,
        prompt=prompt,
        keywords=llm_validation_response.keywords,
        created_at=now,
        expires_at=expire_date
    )
    
    llm_validation.alert_chat_id = new_alert_chat.id
    db.add(new_alert_chat)
    
    await db.commit()
    await db.refresh(new_alert_chat)
    
    asyncio.create_task(
        generate_and_save_alert_chat_embeddings(
            new_alert_chat.id,
            prompt,
        )
    )
    
    expire_date_str : str = expire_date.strftime("%d/%m/%y")
    keyword_hashtags : str = " ".join([f"#{keyword}" for keyword in llm_validation_response.keywords])
    
    return f"Got it! Alert created. Id: {new_alert_chat.id}, will be active until {expire_date_str} {keyword_hashtags}"

@router.patch(
    "/{alert_id}/cancel",
    status_code=status.HTTP_200_OK,
    response_model=str,
    description="Mark an alert as CANCELLED. We do not 'delete' the alert") #Not for billing purposes, but for metrics
async def cancel_alert_chat(alert_id: str, telegram_id: str, db: AsyncSession = Depends(get_db)):
        
    stmt = select(AlertChat).where(
        AlertChat.id == alert_id,
        AlertChat.telegram_id == telegram_id
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        return "That alert does not exist"
    
    alert.status = AlertChatStatus.CANCELLED
    await db.commit()
    
    return "Alert cancelled!"
    

@router.get(
    "/",
    response_model=str,
    description="List all active alerts"
)
async def list_alerts_chats(telegram_id: str, db: AsyncSession = Depends(get_db)):
    
    stmt = select(AlertChat).where(
        AlertChat.telegram_id == telegram_id,
        AlertChat.status == AlertChatStatus.ACTIVE or AlertChat.status == AlertChatStatus.WARNED,
        AlertChat.created_at >= datetime.now()
    )
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    if not alerts:
        return "There are no active alerts."
    
    alert_strings = []
    for alert in alerts:
        expires_at_str = alert.expires_at.strftime("%d/%m/%y")
        alert_string = f"Id: {alert.id}. Expires At: {expires_at_str}. Prompt: {alert.prompt}."
        alert_strings.append(alert_string)
    
    return "\n".join(alert_strings)
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from app.utils.llm_validator import is_alert_chat_duplicated, get_llm_validation
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.env import FLAGSHIP_MODEL, LLM_VALIDATION_THRESHOLD
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
from app.core.config import settings
from app.utils.telegram_message import send_message
from sqlalchemy import or_

logger = logging.getLogger(__name__)

router = APIRouter()

async def create_alert_chat(
    command_text: str, 
    telegram_id: str, 
    db: AsyncSession,
    username: str = None,
    language_code: str = None,
    first_name: str = "Unknown",
    last_name: str = ""
):
    prompt = command_text.replace("/create", "").strip()
    
    if not prompt:
        message = "Please provide a prompt after /create"
        await send_message(telegram_id, message)
        return message
    
    is_duplicated = await is_alert_chat_duplicated(prompt, telegram_id, db)
    if is_duplicated:
        message = "That Alert is already active"
        await send_message(telegram_id, message)
        return message
    
    await send_message(telegram_id, "Ok, let me see.........")
    
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

    if not llm_validation_response.approval or llm_validation_response.chance_score < LLM_VALIDATION_THRESHOLD:
        message = "I'm sorry, I cannot create an alert for that\n\n<b>Reason:</b> " + llm_validation_response.reason

        await send_message(telegram_id, message)
        return message
    
    expire_date = (now + timedelta(days=30)).replace(hour=23, minute=59, second=59)
        
    new_alert_chat = AlertChat(
        id=str(uuid.uuid4()),
        telegram_id=telegram_id,
        prompt=prompt,
        keywords=llm_validation_response.keywords,
        username=username,
        language_code=language_code,
        first_name=first_name,
        last_name=last_name,
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
    
    expire_date_str = expire_date.strftime("%d/%m/%y")
    keyword_hashtags = " ".join([f"#{keyword}" for keyword in llm_validation_response.keywords])
    
    message = f"Got it! Alert created!\nWill be active until <b>{expire_date_str}</b>\n\n<b>{keyword_hashtags}</b>"
    
    await send_message(telegram_id, message)
    return message
    

async def cancel_alert_chat(command_text: str, telegram_id: str, db: AsyncSession):
    alert_id = command_text.replace("/cancel", "").strip()
    
    if not alert_id:
        message = "Please provide an alert ID after <b>/cancel</b>"
        await send_message(telegram_id, message)
        return message
    
    stmt = select(AlertChat).where(
        AlertChat.id == alert_id,
        AlertChat.telegram_id == telegram_id
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()
    
    if not alert:
        message = "That alert does not exist."
        await send_message(telegram_id, message)
        return message
    
    alert.status = AlertChatStatus.CANCELLED
    await db.commit()
    
    message = "Alert cancelled!"
    await send_message(telegram_id, message)
    return message


async def list_alerts_chats(telegram_id: str, db: AsyncSession):
    stmt = select(AlertChat).where(
        AlertChat.telegram_id == telegram_id,
        or_(AlertChat.status == AlertChatStatus.ACTIVE, AlertChat.status == AlertChatStatus.WARNED),
        AlertChat.expires_at > datetime.now()
    )
    
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    if not alerts:
        message = "There are no active alerts."
        await send_message(telegram_id, message)
        return message

    alert_strings = []
    for alert in alerts:
        expires_at_str = alert.expires_at.strftime("%d/%m/%y")
        alert_string = f"<b>Alert</b>: {alert.prompt}\n<b>Expires At: {expires_at_str}\nId</b>: {alert.id}\n\n"
        alert_strings.append(alert_string)
    
    message = "\n".join(alert_strings)
    await send_message(telegram_id, message)
    return message


@router.post("/webhook/{token}")
async def handle_telegram_webhook(
    token: str,
    update: dict,
    db: AsyncSession = Depends(get_db)
):
    if token != settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot token"
        )
    
    message = update.get("message", {})
    if not message:
        return {"error": "No message found in update"}
    
    text = message.get("text", "")
    if not text:
        return {"error": "No text found in message"}
    
    from_user = message.get("from", {})
    telegram_id = str(from_user.get("id"))
    if not telegram_id:
        return {"error": "No user ID found in message"}
    
    username = from_user.get("username")
    language_code = from_user.get("language_code")
    first_name = from_user.get("first_name", "Unknown")
    last_name = from_user.get("last_name", "")
    
    if text.startswith("/create"):
        if len(text) < 17:
            message = "Your request is too brief."
            await send_message(telegram_id, message)
            return message
        
        return await create_alert_chat(text, telegram_id, db, username, language_code, first_name, last_name)
    elif text.startswith("/cancel"):
        return await cancel_alert_chat(text, telegram_id, db)
    elif text.startswith("/list"):
        return await list_alerts_chats(telegram_id, db)
    else:
        message = "Unknown command. Use <b>/create</b>, <b>/cancel</b>, or <b>/list</b>"
        await send_message(telegram_id, message)
        return message
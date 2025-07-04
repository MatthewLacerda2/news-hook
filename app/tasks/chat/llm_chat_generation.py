from app.models.alert_chat import AlertChat
from app.models.llm_models import LLMModel
from app.tasks.llm_apis.gemini import get_gemini_alert_generation
from app.schemas.chat_event import ChatEvent
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert_event import AlertEvent
from app.utils.sourced_data import SourcedData
from app.utils.count_tokens import count_tokens
import httpx
import logging
import json
from httpx import HTTPTransport
from app.core.config import settings

logger = logging.getLogger(__name__)

async def generate_and_send_alert_chat(alert_chat: AlertChat, sourced_document: SourcedData, llm_model: LLMModel, db: AsyncSession):
    
    generated_response = get_gemini_alert_generation(
        sourced_document.content,
        False,
        alert_chat.prompt,
        llm_model.model_name
    )
    
    response_status_code = await send_alert_chat(generated_response, alert_chat.telegram_id, db)
    
    llm_generation_result = ChatEvent(
        id=str(uuid.uuid4()),
        document_id=sourced_document.id,
        alert_chat_id=alert_chat.id,
        triggered_at=datetime.now(),
    )
    await save_alert_event(llm_generation_result, generated_response, response_status_code, llm_model, db)
    
    await db.commit()

async def send_alert_chat(generated_response: str, telegram_id: str, db: AsyncSession) -> int:
    
    logger.info(f"Sending alert_chat to telegram_id {telegram_id}: {generated_response[:34]}...")
    
    transport = HTTPTransport()
    with httpx.Client(transport=transport, timeout=10) as client:
        
        json = {
            "chat_id": telegram_id,
            "text": generated_response
        }
        telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        response : httpx.Response = client.post(telegram_url, json=json)

    return response.status_code

async def save_alert_event(alert_event: ChatEvent, generated_response: str, response_status_code: int, llm_model: LLMModel, db: AsyncSession) -> AlertEvent:

    input_tokens = count_tokens(generated_response, llm_model.model_name)
    output_tokens = count_tokens(generated_response, llm_model.model_name)
    
    alert_event_db = AlertEvent(
        id=alert_event.id,
        alert_chat_id=alert_event.alert_chat_id,
        scraped_data_id=alert_event.document_id,
        triggered_at=alert_event.triggered_at,
        structured_data=json.loads(generated_response),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_price=input_tokens * (llm_model.input_token_price/1000),
        output_price=output_tokens * (llm_model.output_token_price/1000),
        status_code=response_status_code
    )
    db.add(alert_event_db)
    await db.commit()
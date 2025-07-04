import httpx
from httpx import HTTPTransport
from app.core.config import settings

import logging

logger = logging.getLogger(__name__)

async def send_message(telegram_id: str, message: str) -> int:
    
    logger.info(f"Sending message to telegram_id {telegram_id}: {message[:34]}...")
    
    transport = HTTPTransport()
    with httpx.Client(transport=transport, timeout=10) as client:
        telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        json = {
            "chat_id": telegram_id,
            "text": message
        }
        response : httpx.Response = client.post(telegram_url, json=json)
        
    logger.info(f"Telegram response: {response}")
        
    return response.status_code
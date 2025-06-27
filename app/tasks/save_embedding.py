from app.tasks.llm_apis.gemini import get_gemini_embeddings
from app.core.database import get_db
from app.models.alert_prompt import AlertPrompt
from app.models.monitored_data import MonitoredData
from sqlalchemy import select
import logging
import numpy as np
from app.models.alert_chat import AlertChat

logger = logging.getLogger(__name__)

async def generate_and_save_alert_embeddings(alert_id, prompt):
    prompt_embedding = get_gemini_embeddings(prompt, "RETRIEVAL_QUERY")
    await save_alert_embeddings_to_db(alert_id, prompt_embedding)
    
async def generate_and_save_alert_chat_embeddings(alert_chat_id, prompt):
    prompt_embedding = get_gemini_embeddings(prompt, "RETRIEVAL_QUERY")
    await save_alert_chat_embeddings_to_db(alert_chat_id, prompt_embedding)

async def generate_and_save_document_embeddings(document_id : str, content : str):
    document_embedding = get_gemini_embeddings(content, "RETRIEVAL_DOCUMENT")
    await save_document_embeddings_to_db(document_id, document_embedding)

async def save_alert_embeddings_to_db(alert_id, prompt_embedding):
    async for session in get_db():
        result = await session.execute(
            select(AlertPrompt).where(AlertPrompt.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.prompt_embedding = prompt_embedding
            await session.commit()
            break  # Only need one session
        else:
            logger.error(f"Alert with id {alert_id} not found")
            raise ValueError(f"Alert with id {alert_id} not found")
    
    logger.info(f"Alert embedding saved to db")
    
async def save_alert_chat_embeddings_to_db(alert_chat_id, prompt_embedding):
    async for session in get_db():
        result = await session.execute(
            select(AlertChat).where(AlertChat.id == alert_chat_id)
        )
        alert_chat = result.scalar_one_or_none()
        
        if alert_chat:
            alert_chat.prompt_embedding = prompt_embedding
            await session.commit()
            break  # Only need one session
        else:
            logger.error(f"Alert chat with id {alert_chat_id} not found")
            raise ValueError(f"Alert chat with id {alert_chat_id} not found")
        

async def save_document_embeddings_to_db(document_id: str, document_embedding: np.ndarray):
    async for session in get_db():
        result = await session.execute(
            select(MonitoredData).where(MonitoredData.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if document:
            document.content_embedding = document_embedding
            await session.commit()
            break  # Only need one session
        else:
            logger.error(f"Document with id {document_id} not found")
            raise ValueError(f"Document with id {document_id} not found")

import logging
import numpy as np
from typing import List 
from datetime import datetime
from sqlalchemy import select
from app.models.llm_models import LLMModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.monitored_data import DataSource
from app.utils.sourced_data import SourcedData
from app.utils.env import DATA_SIMILARITY_THRESHOLD
from app.models.llm_verification import LLMVerification
from app.models.alert_chat import AlertChat, AlertChatStatus
from app.tasks.llm_apis.gemini import get_gemini_embeddings
from app.tasks.chat.llm_chat_verification import verify_document_matches_alert_chat


logger = logging.getLogger(__name__)


async def vector_search_chat(sourced_document: SourcedData):
    """
    Process a document from a webscrape source and store it in the vector database.
    For each ACTIVE alert that has matching keywords, perform vector similarity search
    to determine if the document is relevant to the alert's intent.
    """
    db = AsyncSessionLocal()
    
    logger.info(f"Getting document embedding for document: {sourced_document.name}")
    
    document_embedding = sourced_document.content_embedding
    if document_embedding is None or np.all(document_embedding == 0):
        document_embedding = get_gemini_embeddings(sourced_document.content, "RETRIEVAL_DOCUMENT")
    
    logger.info(f"Performing vector search for document: {sourced_document.name}")
    
    active_alerts = await find_matching_alert_chats(db, document_embedding, sourced_document.content)
    
    logger.info(f"Found {len(active_alerts)} active alerts for document: {sourced_document.name}")
    
    for alert in active_alerts:
        await verify_document_matches_alert_chat(
            alert_id=str(alert.id),
            sourced_document=sourced_document,
        )
    
    for alert in active_alerts:
        logger.info(f"Alert prompt matching: {alert.prompt}")

async def find_matching_alert_chats(db: AsyncSession, document_embedding: np.ndarray, document_content: str) -> List[AlertChat]:
    """
    Find all active or warned alerts that haven't expired, and log their id, prompt, and cosine similarity to the document.
    """
    conditions = [
        (AlertChat.status == AlertChatStatus.ACTIVE) | (AlertChat.status == AlertChatStatus.WARNED),
        AlertChat.expires_at > datetime.now(),
        AlertChat.prompt_embedding != None,
    ]
    
    stmt = select(AlertChat).where(*conditions)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    logger.info(f"Found {len(alerts)} active or warned, non-expired alerts")
    
    for alert in alerts:
        chat_emb = np.array(alert.prompt_embedding, dtype=np.float32)
        sim = float(np.dot(document_embedding, chat_emb) / (np.linalg.norm(document_embedding) * np.linalg.norm(chat_emb)))
        logger.info(f"AlertChat id={alert.id}, prompt={alert.prompt}, cosine_similarity={sim}")
    
    filtered_alerts = []
    for alert in alerts:
        if any(keyword.lower() in document_content.lower() for keyword in alert.keywords):
            filtered_alerts.append(alert)
    
    return filtered_alerts
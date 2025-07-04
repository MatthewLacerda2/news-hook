from typing import List
from datetime import datetime
from sqlalchemy import select
import numpy as np
import logging

from app.core.database import AsyncSessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.tasks.llm_verification import verify_document_matches_alert
from app.utils.sourced_data import SourcedData
from app.tasks.llm_apis.gemini import get_gemini_embeddings
from app.models.monitored_data import DataSource
from app.utils.env import DATA_SIMILARITY_THRESHOLD
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def vector_search(sourced_document: SourcedData):
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
    
    agent_controller_id = sourced_document.agent_controller_id if sourced_document.source == DataSource.USER_DOCUMENT else None
    
    logger.info(f"Finding matching alerts for document: {sourced_document.name}")
    
    active_alerts = await find_matching_alerts(db, document_embedding, agent_controller_id, sourced_document.content)
    
    for alert in active_alerts:
        await verify_document_matches_alert(
            alert_id=str(alert.id),
            sourced_document=sourced_document,
        )
    
    for alert in active_alerts:
        logger.info(f"Alert prompt matching: {alert.prompt}")

async def find_matching_alerts(db: AsyncSession, document_embedding: np.ndarray, agent_controller_id: str | None, document_content: str) -> List[AlertPrompt]:
    """
    Find active alerts where the prompt_embedding is similar to the document_embedding using PostgreSQL vector search.
    If agent_controller_id is provided, only return alerts belonging to that controller.
    """
    # Convert numpy array to list and format for PostgreSQL array
    embedding_list = [float(x) for x in document_embedding.tolist()]
    
    conditions = [
        AlertPrompt.status == AlertStatus.ACTIVE or AlertPrompt.status == AlertStatus.WARNED,
        AlertPrompt.expires_at > datetime.now(),
        AlertPrompt.prompt_embedding.cosine_distance(embedding_list) <= DATA_SIMILARITY_THRESHOLD,
    ]
    
    if agent_controller_id is not None:
        conditions.append(AlertPrompt.agent_controller_id == agent_controller_id)
    
    stmt = select(AlertPrompt).where(*conditions)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    filtered_alerts = []
    
    for alert in alerts:
        if any(keyword.lower() in document_content.lower() for keyword in alert.keywords):
            filtered_alerts.append(alert)
            
    return filtered_alerts
    
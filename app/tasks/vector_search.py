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
from app.utils.env import DATA_SIMILARITY_THRESHOLD
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def perform_embed_and_vector_search(sourced_document: SourcedData):
    """
    Process a document from a webscrape source and store it in the vector database.
    For each ACTIVE alert that has matching keywords, perform vector similarity search
    to determine if the document is relevant to the alert's intent.
    
    Args:
        md_document: The markdown text to process, as returned by docling
        source_id: The ID of the webscrape source that generated this document
    """
    try:
        db = AsyncSessionLocal()
        
        logger.info(f"Performing vector search for document: {sourced_document.name}")
        
        document_embedding = sourced_document.content_embedding
        if document_embedding is None or np.all(document_embedding == 0):
            document_embedding = await get_gemini_embeddings(sourced_document.content, "RETRIEVAL_DOCUMENT")
        
        active_alerts = await find_matching_alerts(db, document_embedding, sourced_document.agent_controller_id)
        active_alerts = filter_by_keywords(active_alerts, sourced_document.content)
        
        logger.info(f"Found {len(active_alerts)} matching alerts before keywords")
        
        for alert in active_alerts:
            await verify_document_matches_alert(
                alert_id=str(alert.id),
                sourced_document=sourced_document,
            )
            
        logger.info(f"Completed vector search for document: {sourced_document.name}")
                
    except Exception as e:
        logger.error(f"Error in vector search processing: {str(e)}", exc_info=True)
    finally:
        await db.close()

async def find_matching_alerts(db: AsyncSession, document_embedding: np.ndarray, agent_controller_id: str | None) -> List[AlertPrompt]:
    """
    Find active alerts where the prompt_embedding is similar to the document_embedding using PostgreSQL vector search.
    If agent_controller_id is provided, only return alerts belonging to that controller.
    """
    # Convert numpy array to list and format for PostgreSQL array
    embedding_list = [float(x) for x in document_embedding.tolist()]
    
    conditions = [
        AlertPrompt.status == AlertStatus.ACTIVE,
        AlertPrompt.expires_at > datetime.now(),
        AlertPrompt.prompt_embedding.cosine_distance(embedding_list) < DATA_SIMILARITY_THRESHOLD
    ]
    
    if agent_controller_id is not None:
        conditions.append(AlertPrompt.agent_controller_id == agent_controller_id)
    
    stmt = select(AlertPrompt).where(*conditions)
    result = await db.execute(stmt)
    return result.scalars().all()

def filter_by_keywords(alerts: List[AlertPrompt], document_content: str) -> List[AlertPrompt]:
    """
    Filter alerts by checking if any of their keywords appear in the document content.
    
    Args:
        alerts: List of AlertPrompt objects to filter
        document_content: The document text to check against
        
    Returns:
        List of AlertPrompt objects where at least one keyword appears in the document
    """
    filtered_alerts = []
    
    for alert in alerts:
        if any(keyword.lower() in document_content.lower() for keyword in alert.keywords):
            filtered_alerts.append(alert)
            
    return filtered_alerts
    
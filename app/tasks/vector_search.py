from typing import List
from datetime import datetime
from sqlalchemy import select, text
import numpy as np
import logging
from pgvector.sqlalchemy import Vector

from app.core.database import AsyncSessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.tasks.llm_verification import verify_document_matches_alert
from app.utils.sourced_data import SourcedData
from app.tasks.llm_apis.ollama import get_nomic_embeddings
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
        
        document_embedding = await get_nomic_embeddings(sourced_document.content)
        
        active_alerts = await find_matching_alerts_by_embedding(db, document_embedding, sourced_document.agent_controller_id)
        
        logger.info(f"Found {len(active_alerts)} matching alerts before keywords")
        #active_alerts = sort_alerts_by_keyword_overlap(active_alerts)
        #logger.info(f"Found {len(active_alerts)} matching alerts after keywords")
        
        for alert in active_alerts:
            await verify_document_matches_alert(
                alert_id=str(alert.id),
                sourced_document=sourced_document,
            )
            
        logger.info(f"Completed vector search for document: {sourced_document.name}")
                
    except Exception as e:
        # Log error but don't raise to avoid breaking the scraping pipeline
        logger.error(f"Error in vector search processing: {str(e)}", exc_info=True)
    finally:
        await db.close()

async def find_matching_alerts_by_embedding(db: AsyncSession, document_embedding: np.ndarray, agent_controller_id: str | None) -> List[AlertPrompt]:
    """
    Find active alerts where the prompt_embedding is similar to the document_embedding using PostgreSQL vector search.
    If agent_controller_id is provided, only return alerts belonging to that controller.
    """
    # Convert numpy array to list and format for PostgreSQL array
    embedding_list = [float(x) for x in document_embedding.tolist()]
    
    conditions = [
        AlertPrompt.status == AlertStatus.ACTIVE,
        AlertPrompt.expires_at > datetime.now(),
        AlertPrompt.prompt_embedding.cosine_distance(embedding_list) < 0.99  # Use pgvector's SQLAlchemy integration
    ]
    
    if agent_controller_id is not None:
        conditions.append(AlertPrompt.agent_controller_id == agent_controller_id)
    
    stmt = select(AlertPrompt).where(*conditions)
    result = await db.execute(stmt)  # No need for params() since we're using SQLAlchemy's vector type
    return result.scalars().all()
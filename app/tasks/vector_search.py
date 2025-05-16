from typing import List
from datetime import datetime
from sqlalchemy import select, text
import numpy as np
import logging

from app.core.database import SessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.tasks.llm_verification import verify_document_matches_alert
from app.utils.sourced_data import SourcedData
from app.tasks.llm_apis.ollama import get_nomic_embeddings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def process_document_for_vector_search(sourced_document: SourcedData):
    """
    Process a document from a webscrape source and store it in the vector database.
    For each ACTIVE alert that has matching keywords, perform vector similarity search
    to determine if the document is relevant to the alert's intent.
    
    Args:
        md_document: The markdown text to process, as returned by docling
        source_id: The ID of the webscrape source that generated this document
    """
    try:
        db = SessionLocal()
        
        document_embedding = await get_nomic_embeddings(sourced_document.content)
        
        active_alerts = await find_matching_alerts_by_embedding(db, document_embedding, sourced_document.agent_controller_id)
        active_alerts = sort_alerts_by_keyword_overlap(active_alerts)
        
        for alert in active_alerts:
            await verify_document_matches_alert(
                alert_id=str(alert.id),
                document=sourced_document,
            )
                
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
    embedding_list = document_embedding.tolist()
    conditions = [
        AlertPrompt.status == AlertStatus.ACTIVE,
        AlertPrompt.expires_at > datetime.now(),
        text(f"prompt_embedding <=> :embedding <= {1 - 0.85}")
    ]
    
    if agent_controller_id is not None:
        conditions.append(AlertPrompt.agent_controller_id == agent_controller_id)
    
    stmt = select(AlertPrompt).where(*conditions).params(embedding=embedding_list)
    result = await db.execute(stmt)
    return result.scalars().all()

def count_keyword_matches(alert_keywords, reference_keywords):
    count = 0
    for ref_kw in reference_keywords:
        for kw in alert_keywords:
            if ref_kw in kw or kw in ref_kw:
                count += 1
                break  # Only count one match per reference keyword
    return count

def sort_alerts_by_keyword_overlap(active_alerts):
    if not active_alerts:
        return []

    reference_keywords = active_alerts[0].keywords or []
    # Ensure all keywords are strings
    reference_keywords = [str(k) for k in reference_keywords]

    def match_count(alert):
        alert_keywords = alert.keywords or []
        alert_keywords = [str(k) for k in alert_keywords]
        return count_keyword_matches(alert_keywords, reference_keywords)

    sorted_alerts = [active_alerts[0]] + sorted(
        active_alerts[1:], key=match_count, reverse=True
    )
    return sorted_alerts

from typing import List
from datetime import datetime
from sqlalchemy import select
import numpy as np

from app.core.database import SessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.tasks.llm_verification import verify_document_matches_alert
from app.models.agent_controller import AgentController
from app.utils.sourced_data import SourcedData
from app.tasks.llm_apis.ollama import get_nomic_embeddings
from sqlalchemy.ext.asyncio import AsyncSession

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
        
        active_alerts = await find_matching_alerts(db, sourced_document.content)
        
        for alert in active_alerts:
            document_embedding = await get_nomic_embeddings(sourced_document.content)
            
            similarity_score = calculate_cosine_similarity(
                document_embedding, 
                alert.prompt_embedding
            )
            
            if similarity_score >= 0.85:
                await verify_document_matches_alert(
                    alert_id=str(alert.id),
                    document=sourced_document,
                )
                
    except Exception as e:
        # Log error but don't raise to avoid breaking the scraping pipeline
        print(f"Error in vector search processing: {str(e)}")
    finally:
        await db.close()

async def find_matching_alerts(db: AsyncSession, document_content: str) -> List[AlertPrompt]:
    """Find active alerts where all keywords are present in the document and user has sufficient credits"""
    active_alerts = db.execute(
        select(AlertPrompt).where(
            AlertPrompt.status == AlertStatus.ACTIVE,
            AlertPrompt.expires_at > datetime.now()
        )
    ).scalars().all()
    
    matching_alerts = []
    for alert in active_alerts:
        stmt = select(AgentController).where(AgentController.id == alert.agent_controller_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user and user.credit_balance > 0:
            alert_keywords = set(alert.keywords)
            if alert_keywords.issubset(document_content):
                matching_alerts.append(alert)
            
    return matching_alerts

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

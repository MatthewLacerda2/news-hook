from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
import numpy as np

from app.core.database import SessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.tasks.llm_verification import verify_document_matches_alert
from app.models.agent_controller import AgentController

async def process_document_for_vector_search(md_document: Dict[str, Any], source_id: str):
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
        
        # Get active alerts where all keywords are present in the document
        active_alerts = await find_matching_alerts(db, md_document)
        
        # For each matching alert, do vector similarity check
        for alert in active_alerts:
            document_embedding = np.zeros(384)
            
            # Calculate cosine similarity
            similarity_score = calculate_cosine_similarity(
                document_embedding, 
                alert.prompt_embedding
            )
            
            if similarity_score > 0.85:
                await verify_document_matches_alert(
                    alert_id=str(alert.id),
                    document=md_document,
                    similarity_score=similarity_score
                )
                
    except Exception as e:
        # Log error but don't raise to avoid breaking the scraping pipeline
        print(f"Error in vector search processing: {str(e)}")
    finally:
        db.close()

async def find_matching_alerts(db: Session, document_keywords: set) -> List[AlertPrompt]:
    """Find active alerts where all keywords are present in the document and user has sufficient credits"""
    active_alerts = db.execute(
        select(AlertPrompt).where(
            AlertPrompt.status == AlertStatus.ACTIVE,
            AlertPrompt.expires_at > datetime.now()
        )
    ).scalars().all()
    
    # Filter alerts where user has sufficient credits and all keywords match
    matching_alerts = []
    for alert in active_alerts:
        # Check user credits first - most common case
        user = db.query(AgentController).filter(
            AgentController.id == alert.user_id
        ).first()
        
        if user and user.credits > 0:
            # Only check keywords if user has credits
            alert_keywords = set(alert.keywords)
            if alert_keywords.issubset(document_keywords):
                matching_alerts.append(alert)
            
    return matching_alerts

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

import asyncio
import logging
import requests
from datetime import datetime, time
from typing import List
from sqlalchemy import select
from docling.document_converter import DocumentConverter
import uuid
from app.core.database import AsyncSessionLocal
from app.models.webscrape_source import WebscrapeSource
from app.tasks.vector_search import perform_embed_and_vector_search
from app.models.alert_prompt import Alert, AlertStatus
from app.utils.sourced_data import SourcedData, DataSource
from app.utils.env import NUM_EMBEDDING_DIMENSIONS
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.monitored_data import MonitoredData
from app.tasks.llm_apis.gemini import get_gemini_embeddings

logger = logging.getLogger(__name__)

async def process_webscrape_source(source: WebscrapeSource, db: AsyncSession):
    """Process a single webscrape source"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Accept-Language': 'pt-BR, pt;q=0.9, en;q=0.8'
        }
        headers = source.headers or headers
        response = requests.get(
            source.url, 
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        
        converter = DocumentConverter()
        result = converter.convert(response.text).document.export_to_markdown()
        
        source.last_scraped_at = datetime.now()
        source.num_scrapes += 1
        await db.commit()
        
        sourced_data = SourcedData(
            source=DataSource.WEBSCRAPE,
            source_id=source.id,
            document_id=source.id,  #TODO: Change to the document id
            name=result.title,
            content=result,
            content_embedding=np.zeros(NUM_EMBEDDING_DIMENSIONS),
            agent_controller_id=None
        )
        
        await perform_embed_and_vector_search(sourced_document=sourced_data)
        
    except Exception as e:
        # Don't raise the exception - we want to continue with other sources
        logger.error(f"Error processing source {source.id}: {str(e)}", exc_info=True)
        
async def check_and_process_sources():
    """Check for sources that need to be scraped and process them"""
    try:
        db = AsyncSessionLocal()
        now = datetime.now()
        
        query = select(WebscrapeSource).where(
            WebscrapeSource.is_active == True,
            (
                WebscrapeSource.last_scraped_at.is_(None) |
                (
                    now >= 
                    WebscrapeSource.last_scraped_at + 
                    WebscrapeSource.scrape_seconds_interval
                )
            )
        )
        
        result = await db.execute(query)
        sources: List[WebscrapeSource] = result.scalars().all()
        
        tasks = [process_webscrape_source(source, db) for source in sources]
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"Error in check_and_process_sources: {str(e)}", exc_info=True)
    finally:
        await db.close()

def is_night_time() -> bool:
    """Check if current time is between 11 PM and 7 AM"""
    current_time = datetime.now().time()
    night_start = time(23, 0)
    night_end = time(7, 0)
    
    if night_start <= current_time or current_time <= night_end:
        return True
    return False

async def mark_expired_alerts():
    """Mark expired alerts as expired"""
    db = AsyncSessionLocal()
    try:
        stmt = select(Alert).where(Alert.expires_at < datetime.now())
        result = await db.execute(stmt)
        expired_alerts = result.scalars().all()
        
        for alert in expired_alerts:
            alert.status = AlertStatus.EXPIRED
        await db.commit()
    finally:
        await db.close()

async def run_periodic_check(day_interval: int = 60 * 10, night_interval: int = 60 * 30):
    """
    Run the periodic check every interval_seconds
    
    Args:
        day_interval: Interval in seconds during day (7 AM - 11 PM)
        night_interval: Interval in seconds during night (11 PM - 7 AM)
    """
    await mark_expired_alerts()
    await check_and_process_sources()

async def handle_periodic_check_http(request):
    """
    HTTP handler for Cloud Run to process periodic checks.
    This endpoint should be triggered by Cloud Scheduler.
    """
    try:
        # Determine interval based on time of day
        interval = 60 * 30 if is_night_time() else 60 * 10  # 30 min at night, 10 min during day
        
        await run_periodic_check()
        return {"status": "success", "next_interval_seconds": interval}
    except Exception as e:
        logger.error(f"Error in periodic check HTTP handler: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}, 500

async def process_manual_document(
    name: str,
    content: str,
    db: AsyncSession
) -> None:
    """
    Process a manually scraped document through the embedding and vector search pipeline.
    
    Args:
        name: Title/name of the document
        content: The document content in markdown format
        db: Database session
    """
    
    document_id = str(uuid.uuid4())
    
    try:
        content_embedding = await get_gemini_embeddings(content, "RETRIEVAL_DOCUMENT")
        
        monitored_data = MonitoredData(
            id=document_id,
            source=DataSource.MANUAL_DOCUMENT,
            name=name,
            content=content,
            content_embedding=content_embedding,
            agent_controller_id=None
        )
        
        db.add(monitored_data)
        await db.commit()
        await db.refresh(monitored_data)
        
        sourced_data = SourcedData(
            source=DataSource.WEBSCRAPE,
            document_id=monitored_data.id,
            name=name,
            content=content,
            content_embedding=content_embedding,
            agent_controller_id=None
        )
        
        await perform_embed_and_vector_search(sourced_document=sourced_data)
        
    except Exception as e:
        logger.error(f"Error processing manual document {document_id}: {str(e)}", exc_info=True)
        raise  # In manual processing, you probably want to know if it failed

if __name__ == "__main__":
    # For local development testing only
    asyncio.run(run_periodic_check())

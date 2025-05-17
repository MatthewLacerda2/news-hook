import asyncio
import logging
import requests
from datetime import datetime, time
from typing import List
from sqlalchemy import select
from docling.document_converter import DocumentConverter

from app.core.database import AsyncSessionLocal
from app.models.webscrape_source import WebscrapeSource
from app.tasks.vector_search import perform_embed_and_vector_search
from app.models.alert_prompt import Alert, AlertStatus
from app.utils.sourced_data import SourcedData, DataSource
from app.utils.env import NUM_EMBEDDING_DIMENSIONS
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

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
            source_url=source.url,
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
    while True:
        await mark_expired_alerts()
        await check_and_process_sources()
        interval = night_interval if is_night_time() else day_interval
        await asyncio.sleep(interval)

if __name__ == "__main__":
    #TODO: call this at startup when ready for production
    asyncio.run(run_periodic_check())

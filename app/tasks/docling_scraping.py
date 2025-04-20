import asyncio
import logging
import requests
from datetime import datetime
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from docling.document_converter import DocumentConverter

from app.core.database import SessionLocal
from app.models.webscrape_source import WebscrapeSource
from app.tasks.vector_search import process_document_for_vector_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_webscrape_source(source: WebscrapeSource, db: Session):
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
        
        # Convert using docling
        converter = DocumentConverter()
        result = converter.convert(response.text).document.export_to_markdown()
        
        source.last_scraped_at = datetime.now()
        source.num_scrapes += 1
        db.commit()
        
        await process_document_for_vector_search(
            document=result.document.to_dict(),
            source_id=str(source.id)
        )
        
    except Exception as e:
        logger.error(f"Error processing source {source.id}: {str(e)}")
        # Don't raise the exception - we want to continue with other sources
        
async def check_and_process_sources():
    """Check for sources that need to be scraped and process them"""
    try:
        db = SessionLocal()
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
        
        sources: List[WebscrapeSource] = db.execute(query).scalars().all()
        
        tasks = [process_webscrape_source(source, db) for source in sources]
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"Error in check_and_process_sources: {str(e)}")
    finally:
        db.close()

async def run_periodic_check(interval_seconds: int = 60):
    """Run the periodic check every interval_seconds"""
    while True:
        await check_and_process_sources()
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    asyncio.run(run_periodic_check())

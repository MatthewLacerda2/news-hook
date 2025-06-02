import asyncio
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.monitored_data import MonitoredData
from app.utils.sourced_data import SourcedData, DataSource
from app.tasks.vector_search import perform_embed_and_vector_search
from app.tasks.llm_apis.gemini import get_gemini_embeddings

logger = logging.getLogger(__name__)

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
        content_embedding = get_gemini_embeddings(content, "RETRIEVAL_DOCUMENT")
        
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
            source=DataSource.MANUAL_DOCUMENT,
            document_id=monitored_data.id,
            name=name,
            content=content,
            content_embedding=content_embedding,
            agent_controller_id=None
        )
        
        await perform_embed_and_vector_search(sourced_document=sourced_data)
        
    except Exception as e:
        logger.error(f"Error processing manual document {document_id}: {str(e)}", exc_info=True)
        raise
from app.tasks.llm_apis.ollama import get_nomic_embeddings
from app.core.database import get_db
from app.models.alert_prompt import AlertPrompt
from app.models.user_document import UserDocument
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

async def generate_and_save_alert_embeddings(alert_id, prompt):
    prompt_embedding = await get_nomic_embeddings(prompt)
    await save_embeddings_to_db(alert_id, prompt_embedding)

async def save_embeddings_to_db(alert_id, prompt_embedding):
    async for session in get_db():
        result = await session.execute(
            select(AlertPrompt).where(AlertPrompt.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.prompt_embedding = prompt_embedding
            await session.commit()
            break  # Only need one session
        else:
            logger.error(f"Alert with id {alert_id} not found")
            raise ValueError(f"Alert with id {alert_id} not found")
        
async def generate_and_save_document_embeddings(document_id, content):
    document_embedding = await get_nomic_embeddings(content)
    await save_embeddings_to_db(document_id, document_embedding)

async def save_embeddings_to_db(document_id, document_embedding):
    async for session in get_db():
        result = await session.execute(
            select(UserDocument).where(UserDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if document:
            document.content_embedding = document_embedding
            await session.commit()
            break  # Only need one session
        else:
            logger.error(f"Document with id {document_id} not found")
            raise ValueError(f"Document with id {document_id} not found")

from app.tasks.llm_apis.ollama import get_nomic_embeddings
from app.core.database import get_db
from app.models.alert_prompt import AlertPrompt
from sqlalchemy import select

async def generate_and_save_embeddings(alert_id, prompt, parsed_intent):
    prompt_embedding = await get_nomic_embeddings(prompt)
    parsed_intent_embedding = await get_nomic_embeddings(str(parsed_intent))
    await save_embeddings_to_db(alert_id, prompt_embedding, parsed_intent_embedding)

async def save_embeddings_to_db(alert_id, prompt_embedding, parsed_intent_embedding):
    async for session in get_db():
        result = await session.execute(
            select(AlertPrompt).where(AlertPrompt.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.prompt_embedding = prompt_embedding
            alert.parsed_intent_embedding = parsed_intent_embedding
            await session.commit()
            break  # Only need one session
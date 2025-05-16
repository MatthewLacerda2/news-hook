from sqlalchemy import select
from datetime import datetime
from app.core.database import SessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.utils.llm_response_formats import LLMVerificationFormat
from app.tasks.llm_apis.ollama import get_ollama_verification
from app.tasks.llm_apis.gemini import get_gemini_verification
from app.tasks.llm_generation import get_llm_generation
from app.utils.sourced_data import SourcedData
from app.utils.count_tokens import count_tokens
from app.models.llm_verification import LLMVerification
from app.models.llm_models import LLMModel
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


async def verify_document_matches_alert(
    alert_id: str,
    sourced_document: SourcedData,
):
    """
    Use LLM to verify if a document actually matches an alert's intent.
    
    Args:
        alert_id: The ID of the alert prompt to verify against
        document: The document to verify, as returned by docling
    """
    try:
        db = SessionLocal()
        
        stmt = select(AlertPrompt).where(AlertPrompt.id == alert_id)
        result = await db.execute(stmt)
        alert_prompt = result.scalar_one_or_none()
        
        verification_result: LLMVerificationFormat
        if alert_prompt.llm_model == "llama3.1":
            verification_result = await get_ollama_verification(
                alert_prompt.prompt,
                sourced_document.content,
            )
        elif alert_prompt.llm_model == "gemini-2.0-flash":
            verification_result = await get_gemini_verification(
                alert_prompt.prompt,
                sourced_document.content,
            )
        else:
            msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
            print(f"Unsupported LLM model: {alert_prompt.llm_model}\n{msg}")
            raise ValueError(f"Unsupported LLM model: {alert_prompt.llm_model}")
        
        await register_llm_verification(alert_prompt, verification_result, alert_prompt.llm_model, db)
            
        if verification_result.approval and verification_result.chance_score >= 0.85:
            await get_llm_generation(alert_prompt, sourced_document, db)
            
            if not alert_prompt.is_recurring:
                alert_prompt.status = AlertStatus.TRIGGERED
            await db.commit()
            
    except Exception as e:
        logger.error(f"Error in LLM verification: {str(e)}", exc_info=True)
    finally:
        await db.close()
        
async def register_llm_verification(alert_prompt: AlertPrompt, verification_result: LLMVerificationFormat, llm_model: str, db: AsyncSession):
    input_tokens_count = count_tokens(alert_prompt.prompt, alert_prompt.llm_model)
    output_tokens_count = count_tokens(verification_result.output, alert_prompt.llm_model)
    
    stmt = select(LLMModel).where(LLMModel.model_name == llm_model)
    result = await db.execute(stmt)
    llm_model_db = result.scalar_one_or_none()
    
    llm_verification = LLMVerification(
        alert_prompt_id=alert_prompt.id,
        approval=verification_result.approval,
        chance_score=verification_result.chance_score,
        input_tokens_count=input_tokens_count,
        input_tokens_price=input_tokens_count * llm_model_db.input_token_price,
        output_tokens_count=output_tokens_count,
        output_tokens_price=output_tokens_count * llm_model_db.output_token_price,
        llm_model=llm_model,
        date_time=datetime.now()
    )
    
    db.add(llm_verification)
    await db.commit()
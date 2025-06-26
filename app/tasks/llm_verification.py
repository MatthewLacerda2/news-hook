from sqlalchemy import select
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.utils.llm_response_formats import LLMVerificationFormat
from app.tasks.llm_apis.gemini import get_gemini_verification
from app.tasks.llm_generation import generate_and_send_alert
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
    """
    try:
        db = AsyncSessionLocal()
        
        stmt = select(AlertPrompt).where(AlertPrompt.id == alert_id)
        result = await db.execute(stmt)
        alert_prompt: AlertPrompt = result.scalar_one()
        
        verification_result = get_gemini_verification(
            alert_prompt.prompt,
            sourced_document.content,
            alert_prompt.llm_model
        )
        
        llm_model_stmt = select(LLMModel).where(LLMModel.model_name == alert_prompt.llm_model)
        llm_model_result = await db.execute(llm_model_stmt)
        llm_model = llm_model_result.scalar_one()
        
        await register_llm_verification(alert_prompt, verification_result, llm_model, sourced_document.id, db)
            
        if verification_result.approval:
            await generate_and_send_alert(alert_prompt, sourced_document, llm_model, db)
            
            if not alert_prompt.is_recurring:
                alert_prompt.status = AlertStatus.TRIGGERED
            await db.commit()
            
    except Exception as e:
        logger.error(f"Error in LLM verification: {str(e)}", exc_info=True)
    finally:
        await db.close()
        
async def register_llm_verification(alert_prompt: AlertPrompt, verification_result: LLMVerificationFormat, llm_model: LLMModel, document_id: str, db: AsyncSession):
    input_tokens_count = count_tokens(alert_prompt.prompt, alert_prompt.llm_model)
    output_tokens_count = count_tokens(verification_result.__str__(), alert_prompt.llm_model)
    
    llm_verification = LLMVerification(
        alert_prompt_id=alert_prompt.id,
        document_id=verification_result.document_id,
        approval=verification_result.approval,
        chance_score=verification_result.chance_score,
        reason=verification_result.reason,
        keywords=verification_result.keywords,
        llm_model=llm_model.model_name,
        input_tokens_count=input_tokens_count,
        input_tokens_price=input_tokens_count * llm_model.input_token_price,
        output_tokens_count=output_tokens_count,
        output_tokens_price=output_tokens_count * llm_model.output_token_price,
        date_time=datetime.now()
    )
    
    db.add(llm_verification)
    await db.commit()
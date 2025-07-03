from sqlalchemy import select
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.models.alert_chat import AlertChat
from app.utils.llm_response_formats import LLMVerificationFormat
from app.tasks.llm_apis.gemini import get_gemini_verification
from app.tasks.chat.llm_chat_generation import generate_and_send_alert_chat
from app.utils.sourced_data import SourcedData
from app.utils.count_tokens import count_tokens
from app.models.llm_verification import LLMVerification
from app.models.llm_models import LLMModel
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.utils.env import FLAGSHIP_MODEL


logger = logging.getLogger(__name__)


async def verify_document_matches_alert_chat(
    alert_id: str,
    sourced_document: SourcedData,
) -> bool:
    """
    Use LLM to verify if a document actually matches an alert chat's intent.
    """
    db = AsyncSessionLocal()
    
    stmt = select(AlertChat).where(AlertChat.id == alert_id)
    result = await db.execute(stmt)
    alert_chat: AlertChat = result.scalar_one()
    
    verification_result = get_gemini_verification(
        alert_chat.prompt,
        sourced_document.content,
        FLAGSHIP_MODEL
    )
    
    llm_model_stmt = select(LLMModel).where(LLMModel.model_name == FLAGSHIP_MODEL)
    llm_model_result = await db.execute(llm_model_stmt)
    llm_model = llm_model_result.scalar_one()
    
    await register_llm_verification(alert_chat, verification_result, llm_model, sourced_document.id, db)
        
    if verification_result.approval:
        await generate_and_send_alert_chat(alert_chat, sourced_document, llm_model, db)
        
    return verification_result.approval

async def register_llm_verification(alert_chat: AlertChat, verification_result: LLMVerificationFormat, llm_model: LLMModel, document_id: str, db: AsyncSession):
    input_tokens_count = count_tokens(alert_chat.prompt, FLAGSHIP_MODEL)
    output_tokens_count = count_tokens(verification_result.__str__(), FLAGSHIP_MODEL)
    
    llm_verification = LLMVerification(
        alert_chat_id=alert_chat.id,
        document_id=document_id,
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
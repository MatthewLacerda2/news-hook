from sqlalchemy import select
from datetime import datetime
from app.core.database import SessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.utils.llm_response_formats import LLMVerificationFormat
from app.tasks.llm_apis.ollama import get_ollama_verification
from app.tasks.llm_apis.gemini import get_gemini_verification
from app.tasks.llm_generation import llm_generation
from app.utils.sourced_data import SourcedData
import tiktoken
from app.models.llm_verification import LLMVerification
from sqlalchemy.orm import Session
from app.models.llm_models import LLMModel

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
        alert_prompt = db.execute(stmt).scalar_one()
        
        # Choose LLM based on model name
        verification_result: LLMVerificationFormat
        if alert_prompt.llm_model == "llama3.1":
            verification_result = get_ollama_verification(
                alert_prompt.prompt,
                alert_prompt.parsed_intent,
            )
        elif alert_prompt.llm_model == "gemini":
            verification_result = await get_gemini_verification(
                alert_prompt.prompt,
                alert_prompt.parsed_intent,
            )
        else:
            msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
            print(f"Unsupported LLM model: {alert_prompt.llm_model}\n{msg}")
            raise ValueError(f"Unsupported LLM model: {alert_prompt.llm_model}")
        
        await register_llm_verification(alert_prompt, verification_result, alert_prompt.llm_model, db)
            
        # Check if verification passes our criteria
        if verification_result.approval and verification_result.chance_score >= 0.85:
            # Pass to LLM generation
            await llm_generation(alert_prompt, sourced_document, db)
            
            # Update alert status
            alert_prompt.status = AlertStatus.TRIGGERED
            db.commit()
            
    except Exception as e:
        print(f"Error in LLM verification: {str(e)}")
    finally:
        db.close()
        
async def register_llm_verification(alert_prompt: AlertPrompt, verification_result: LLMVerificationFormat, llm_model: str, db: Session):
    
    input_tokens_count = tiktoken.count_tokens(alert_prompt.prompt)
    output_tokens_count = tiktoken.count_tokens(verification_result.output)
    
    llm_model_db = db.query(LLMModel).filter(LLMModel.model_name == llm_model).first()
    
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
    db.commit()
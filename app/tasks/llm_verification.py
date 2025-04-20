from typing import Dict, Any
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.alert_prompt import AlertPrompt, AlertStatus
from app.utils.llm_response_formats import LLMVerificationFormat
from app.tasks.llm_apis.ollama import get_ollama_verification
from app.tasks.llm_apis.gemini import get_gemini_verification
from app.tasks.llm_generation import llm_generation

async def verify_document_matches_alert(
    alert_id: str,
    document: Dict[str, Any],
    similarity_score: float
):
    """
    Use LLM to verify if a document actually matches an alert's intent.
    
    Args:
        alert_id: The ID of the alert prompt to verify against
        document: The document to verify, as returned by docling
        similarity_score: The cosine similarity score from vector search
    """
    try:
        db = SessionLocal()
        
        stmt = select(AlertPrompt).where(AlertPrompt.id == alert_id)
        alert_prompt = db.execute(stmt).scalar_one()
        
        # Choose LLM based on model name
        verification_result: LLMVerificationFormat
        if alert_prompt.llm_model == "llama3.1":
            verification_result = await get_ollama_verification(
                alert_prompt.prompt,
                alert_prompt.parsed_intent,
                document
            )
        elif alert_prompt.llm_model == "gemini":
            verification_result = await get_gemini_verification(
                alert_prompt.prompt,
                alert_prompt.parsed_intent,
                document
            )
        else:
            msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
            print(f"Unsupported LLM model: {alert_prompt.llm_model}\n{msg}")
            raise ValueError(f"Unsupported LLM model: {alert_prompt.llm_model}")
            
        # Check if verification passes our criteria
        if verification_result.approval and verification_result.chance_score >= 0.85:
            # Pass to LLM generation
            await llm_generation(alert_prompt, document)
            
            # Update alert status
            alert_prompt.status = AlertStatus.TRIGGERED
            db.commit()
            
    except Exception as e:
        print(f"Error in LLM verification: {str(e)}")
    finally:
        db.close()

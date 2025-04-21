from app.models.alert_prompt import AlertPrompt
from app.tasks.llm_apis.ollama import get_ollama_alert_generation
from app.tasks.llm_apis.gemini import get_gemini_alert_generation
from app.schemas.alert_event import AlertEventResponse
from datetime import datetime
import uuid
from app.core.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from app.models.alert_event import AlertEvent
from app.utils.llm_response_formats import LLMGenerationFormat

async def llm_generation(alert_prompt: AlertPrompt, document: str, db: Session) -> AlertEventResponse:
    
    if alert_prompt.llm_model == "ollama":
        generated_response = get_ollama_alert_generation(
            alert_prompt.parsed_intent,
            document,
            alert_prompt.example_response,
        )
    elif alert_prompt.llm_model == "gemini":
        generated_response = get_gemini_alert_generation(
            alert_prompt.parsed_intent,
            document,
            alert_prompt.example_response,
        )
    else:
        msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
        print(f"Unsupported LLM model: {alert_prompt.llm_model}\n{msg}")
        raise ValueError(f"Unsupported LLM model: {alert_prompt.llm_model}")
    
    llm_generation_result = AlertEventResponse(
        id=uuid.uuid4(),
        alert_prompt_id=alert_prompt.id,
        triggered_at=datetime.now(),
        output=generated_response.output,
        tags=generated_response.tags,
        structured_data=generated_response.structured_data,
    )
    
    save_alert_event(llm_generation_result, generated_response, db)
    
    send_alert_event(llm_generation_result)
    
    return llm_generation_result

def save_alert_event(alert_event: AlertEventResponse, generated_response: LLMGenerationFormat, db: Session) -> AlertEvent:
    alert_event_db = AlertEvent(
        id=alert_event.id,
        alert_prompt_id=alert_event.alert_prompt_id,
        triggered_at=alert_event.triggered_at,
        output=generated_response.output,
        tags=generated_response.tags,
        structured_data=generated_response.structured_data,
    )
    db.add(alert_event_db)
    db.commit()
    db.refresh(alert_event_db)
    return alert_event_db

def send_alert_event(alert_event: AlertEventResponse):
    #TODO: Implement alert event sending
    #just get the alert event's http method, url, and send the response
    pass


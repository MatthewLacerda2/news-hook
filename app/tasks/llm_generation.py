from app.models.alert_prompt import AlertPrompt
from app.tasks.llm_apis.ollama import get_ollama_alert_generation
from app.tasks.llm_apis.gemini import get_gemini_alert_generation
from app.schemas.alert_event import NewsEvent
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from app.models.alert_event import AlertEvent
from app.utils.llm_response_formats import LLMGenerationFormat
import requests

async def llm_generation(alert_prompt: AlertPrompt, document: str, db: Session) -> NewsEvent:
    
    if alert_prompt.llm_model == "ollama":
        generated_response = get_ollama_alert_generation(
            alert_prompt.parsed_intent,
            document,
            alert_prompt.response_format,
        )
    elif alert_prompt.llm_model == "gemini":
        generated_response = get_gemini_alert_generation(
            alert_prompt.parsed_intent,
            document,
            alert_prompt.response_format,
        )
    else:
        msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
        print(f"Unsupported LLM model: {alert_prompt.llm_model}\n{msg}")
        raise ValueError(f"Unsupported LLM model: {alert_prompt.llm_model}")
    
    llm_generation_result = NewsEvent(
        id=uuid.uuid4(),
        alert_prompt_id=alert_prompt.id,
        triggered_at=datetime.now(),
        output=generated_response.output,
        tags=generated_response.tags,
        structured_data=generated_response.structured_data,
    )
        
    send_alert_event(llm_generation_result)
    
    save_alert_event(llm_generation_result, generated_response, db)
    
    return llm_generation_result

def save_alert_event(alert_event: NewsEvent, generated_response: LLMGenerationFormat, db: Session) -> AlertEvent:
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

def send_alert_event(alert_event: NewsEvent, db: Session):
    
    alert_prompt = db.query(AlertPrompt).filter(AlertPrompt.id == alert_event.alert_prompt_id).first()
    
    #TODO: add retries or backoff, and log the fails
    if alert_prompt.http_method == "POST":
        response = requests.post(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
    elif alert_prompt.http_method == "PUT":
        response = requests.put(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
    elif alert_prompt.http_method == "PATCH":
        response = requests.patch(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
    else:
        raise ValueError(f"Unsupported HTTP method: {alert_prompt.http_method}")
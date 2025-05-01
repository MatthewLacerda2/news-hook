from app.models.alert_prompt import AlertPrompt
from app.models.agent_controller import AgentController
from app.models.llm_models import LLMModel
from app.tasks.llm_apis.ollama import get_ollama_alert_generation
from app.tasks.llm_apis.gemini import get_gemini_alert_generation
from app.schemas.alert_event import NewsEvent
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert_event import AlertEvent
from app.utils.llm_response_formats import LLMGenerationFormat
import requests
from app.utils.sourced_data import SourcedData
from app.models.monitored_data import MonitoredData
import tiktoken

async def llm_generation(alert_prompt: AlertPrompt, sourced_document: SourcedData, db: AsyncSession) -> NewsEvent:
    
    if alert_prompt.llm_model == "llama3.1":
        generated_response = await get_ollama_alert_generation(
            alert_prompt.parsed_intent,
            sourced_document.content,
            alert_prompt.response_format,
        )
    elif alert_prompt.llm_model == "gemini":
        generated_response = await get_gemini_alert_generation(
            alert_prompt.parsed_intent,
            sourced_document.content,
            alert_prompt.response_format,
        )
    else:
        msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
        print(f"Unsupported LLM model: {alert_prompt.llm_model}\n{msg}")
        raise ValueError(f"Unsupported LLM model: {alert_prompt.llm_model}")
    
    llm_generation_result = NewsEvent(
        id=str(uuid.uuid4()),
        alert_prompt_id=alert_prompt.id,
        triggered_at=datetime.now(),
        output=generated_response.output,
        tags=generated_response.tags,
        source_url=sourced_document.source_url,
        structured_data=generated_response.structured_data,
    )

    send_alert_event(llm_generation_result)
    
    await save_alert_event(llm_generation_result, generated_response, db)
    await save_monitored_data(sourced_document, db)
    await register_credit_usage(alert_prompt, sourced_document, generated_response, alert_prompt.id, db)
    
    return llm_generation_result

def send_alert_event(alert_event: NewsEvent, db: AsyncSession):
    
    alert_prompt = db.query(AlertPrompt).filter(AlertPrompt.id == alert_event.alert_prompt_id).first()
    
    #TODO: add retries or backoff, and log the failures
    if alert_prompt.http_method == "POST":
        requests.post(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
    elif alert_prompt.http_method == "PUT":
        requests.put(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
    elif alert_prompt.http_method == "PATCH":
        requests.patch(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
    else:
        raise ValueError(f"Unsupported HTTP method: {alert_prompt.http_method}")

async def save_alert_event(alert_event: NewsEvent, generated_response: LLMGenerationFormat, db: AsyncSession) -> AlertEvent:
    alert_event_db = AlertEvent(
        id=alert_event.id,
        alert_prompt_id=alert_event.alert_prompt_id,
        scraped_data_id=alert_event.scraped_data_id,
        triggered_at=alert_event.triggered_at,
        output=generated_response.output,
        tags=generated_response.tags,
        structured_data=generated_response.structured_data
    )
    db.add(alert_event_db)
    db.commit()

async def save_monitored_data(sourced_document: SourcedData, db: AsyncSession):
    monitored_data_db = MonitoredData(
        id=sourced_document.id,
        source=sourced_document.source,
        content=sourced_document.content,
        content_embedding=sourced_document.content_embedding,
    )
    db.add(monitored_data_db)
    db.commit()

async def register_credit_usage(alert_prompt: AlertPrompt, sourced_document: SourcedData, generated_response: LLMGenerationFormat, db: AsyncSession):
    
    input_tokens_count = tiktoken.count_tokens(alert_prompt.prompt) + tiktoken.count_tokens(generated_response.output)
    output_tokens_count = tiktoken.count_tokens(generated_response.output)
    
    # find the alert_prompt based on its id
    alert_prompt_db = db.query(AlertPrompt).filter(AlertPrompt.id == alert_prompt.id).first()
    
    # find the llm_model based on the alert prompt's llm_model
    llm_model_db = db.query(LLMModel).filter(LLMModel.model_name == alert_prompt.llm_model).first()
    # find the agent_controller based on the alert_prompt's agent_controller_id
    agent_controller_db = db.query(AgentController).filter(AgentController.id == alert_prompt_db.agent_controller_id).first()
    
    input_tokens_price = input_tokens_count * (llm_model_db.input_token_price/1000000)
    output_tokens_price = output_tokens_count * (llm_model_db.output_token_price/1000000)
    
    agent_controller_db.credit_balance -= (input_tokens_price + output_tokens_price)
    
    db.commit()
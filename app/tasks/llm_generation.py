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
from app.utils.sourced_data import SourcedData
from app.models.monitored_data import MonitoredData
from app.utils.count_tokens import count_tokens
from sqlalchemy import select
import httpx

async def llm_generation(alert_prompt: AlertPrompt, sourced_document: SourcedData, db: AsyncSession) -> NewsEvent:
    
    if alert_prompt.llm_model == "llama3.1":
        generated_response = await get_ollama_alert_generation(
            sourced_document.content,
            alert_prompt.payload_format,
            sourced_document.source_url
        )
    elif alert_prompt.llm_model == "gemini-2.5-pro-preview-05-06":
        generated_response = await get_gemini_alert_generation(
            sourced_document.content,
            alert_prompt.payload_format,
            sourced_document.source_url
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

    await send_alert_event(llm_generation_result, db)
    
    await save_alert_event(llm_generation_result, generated_response, db)
    await save_monitored_data(sourced_document, db)
    await register_credit_usage(alert_prompt, generated_response, db)
    
    return llm_generation_result

async def send_alert_event(alert_event: NewsEvent, db: AsyncSession):
    
    stmt = select(AlertPrompt).where(AlertPrompt.id == alert_event.alert_prompt_id)
    result = await db.execute(stmt)
    alert_prompt = result.scalar_one_or_none()
    
    #TODO: add retries or backoff
    async with httpx.AsyncClient() as client:
        if alert_prompt.http_method == "POST":
            await client.post(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
        elif alert_prompt.http_method == "PUT":
            await client.put(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
        elif alert_prompt.http_method == "PATCH":
            await client.patch(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
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

async def register_credit_usage(alert_prompt: AlertPrompt, generated_response: LLMGenerationFormat, db: AsyncSession):
    
    input_tokens_count = count_tokens(alert_prompt.prompt, alert_prompt.llm_model)
    output_tokens_count = count_tokens(generated_response.output, alert_prompt.llm_model)
        
    stmt = select(LLMModel).where(LLMModel.model_name == alert_prompt.llm_model)
    result = await db.execute(stmt)
    llm_model_db = result.scalar_one_or_none()
    
    stmt = select(AgentController).where(AgentController.id == alert_prompt.agent_controller_id)
    result = await db.execute(stmt)
    agent_controller_db = result.scalar_one_or_none()
    
    input_tokens_price = input_tokens_count * (llm_model_db.input_token_price/1000000)
    output_tokens_price = output_tokens_count * (llm_model_db.output_token_price/1000000)
    
    agent_controller_db.credit_balance -= (input_tokens_price + output_tokens_price)
    
    db.commit()
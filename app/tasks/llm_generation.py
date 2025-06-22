from app.models.alert_prompt import AlertPrompt
from app.models.agent_controller import AgentController
from app.models.llm_models import LLMModel
from app.tasks.llm_apis.gemini import get_gemini_alert_generation
from app.schemas.news_event import NewsEvent
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert_event import AlertEvent
from app.utils.sourced_data import SourcedData
from app.models.monitored_data import MonitoredData
from app.utils.count_tokens import count_tokens
from sqlalchemy import select
import httpx
import logging
import json
from app.models.alert_prompt import HttpMethod
from urllib3 import Retry
from httpx import HTTPTransport

logger = logging.getLogger(__name__)

async def generate_and_send_alert(alert_prompt: AlertPrompt, sourced_document: SourcedData, llm_model: LLMModel, db: AsyncSession):
    
    generated_response = get_gemini_alert_generation(
        sourced_document.content,
        alert_prompt.payload_format,
        alert_prompt.prompt,
        llm_model.model_name
    )
    
    llm_generation_result = NewsEvent(
        id=str(uuid.uuid4()),
        document_id=sourced_document.id,
        alert_prompt_id=alert_prompt.id,
        triggered_at=datetime.now(),
        output=generated_response,
        tags=alert_prompt.keywords,
        structured_data=json.loads(generated_response)
    )

    await send_alert_event(llm_generation_result, db)
    await save_alert_event(llm_generation_result, generated_response, llm_model, db)
    await register_credit_usage(alert_prompt, generated_response, db)
    
    return llm_generation_result

async def send_alert_event(alert_event: NewsEvent, db: AsyncSession):
    
    stmt = select(AlertPrompt).where(AlertPrompt.id == alert_event.alert_prompt_id)
    result = await db.execute(stmt)
    alert_prompt = result.scalar_one_or_none()
    
    try:
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[status for status in range(400, 600)]
        )
        
        transport = HTTPTransport(retries=retry)
        
        with httpx.Client(transport=transport, timeout=10) as client:
            if alert_prompt.http_method == HttpMethod.POST:
                logger.info(f"Sending {alert_prompt.http_method} to {alert_prompt.http_url} with data: {alert_event.structured_data}")
                response = client.post(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers or {})
            elif alert_prompt.http_method == HttpMethod.PUT:
                logger.info(f"Sending {alert_prompt.http_method} to {alert_prompt.http_url} with data: {alert_event.structured_data}")
                response = client.put(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers or {})
            elif alert_prompt.http_method == HttpMethod.PATCH:
                logger.info(f"Sending {alert_prompt.http_method} to {alert_prompt.http_url} with data: {alert_event.structured_data}")
                response = client.patch(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers or {})
            else:
                raise ValueError(f"Unsupported HTTP method: {alert_prompt.http_method}")
            
            if response.status_code >= 400:
                logger.error(f"Alert webhook failed with status {response.status_code}: {response.text}")
                return str(f"{response.status_code}: {response.text}")
            else:
                return None
            
    except httpx.TimeoutException as e:
        logger.error(f"Timeout while sending alert to {alert_prompt.http_url}: {str(e)}")
    except httpx.ConnectError as e:
        logger.error(f"Connection error while sending alert to {alert_prompt.http_url}: {str(e)}")
    except httpx.RequestError as e:
        status = getattr(e.response, 'status_code', 'unknown')
        logger.error(f"Request error (status {status}) while sending alert to {alert_prompt.http_url}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while sending alert to {alert_prompt.http_url}: {str(e)}")

async def save_alert_event(alert_event: NewsEvent, generated_response: str, llm_model: LLMModel, db: AsyncSession) -> AlertEvent:

    input_tokens = count_tokens(generated_response, llm_model.model_name)
    output_tokens = count_tokens(str(alert_event.structured_data), llm_model.model_name)
    
    alert_event_db = AlertEvent(
        id=alert_event.id,
        alert_prompt_id=alert_event.alert_prompt_id,
        scraped_data_id=alert_event.document_id,
        triggered_at=alert_event.triggered_at,
        structured_data=json.loads(generated_response),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_price=input_tokens * (llm_model.input_token_price/1000),
        output_price=output_tokens * (llm_model.output_token_price/1000)
    )
    db.add(alert_event_db)
    await db.commit()

async def save_document(sourced_document: SourcedData, db: AsyncSession):
    monitored_data_db = MonitoredData(
        id=sourced_document.id,
        source=sourced_document.source,
        name=sourced_document.name,
        content=sourced_document.content,
        content_embedding=sourced_document.content_embedding,
        monitored_datetime=sourced_document.retrieved_datetime,
        agent_controller_id=sourced_document.agent_controller_id,
    )
    db.add(monitored_data_db)
    await db.commit()
    await db.refresh(monitored_data_db)

async def register_credit_usage(alert_prompt: AlertPrompt, generated_response: str, db: AsyncSession):
    
    input_tokens_count = count_tokens(alert_prompt.prompt, alert_prompt.llm_model)
    output_tokens_count = count_tokens(generated_response, alert_prompt.llm_model)
        
    stmt = select(LLMModel).where(LLMModel.model_name == alert_prompt.llm_model)
    result = await db.execute(stmt)
    llm_model_db = result.scalar_one_or_none()
    
    stmt = select(AgentController).where(AgentController.id == alert_prompt.agent_controller_id)
    result = await db.execute(stmt)
    agent_controller_db = result.scalar_one_or_none()
    
    input_tokens_price = input_tokens_count * (llm_model_db.input_token_price/1000000)
    output_tokens_price = output_tokens_count * (llm_model_db.output_token_price/1000000)
    
    agent_controller_db.credit_balance -= (input_tokens_price + output_tokens_price)
    
    await db.commit()
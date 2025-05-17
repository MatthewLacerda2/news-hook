from app.models.alert_prompt import AlertPrompt
from app.models.agent_controller import AgentController
from app.models.llm_models import LLMModel
from app.tasks.llm_apis.ollama import get_ollama_alert_generation
from app.tasks.llm_apis.gemini import get_gemini_alert_generation
from app.schemas.news_event import NewsEvent
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
from app.models.user_document import UserDocument
import logging


logger = logging.getLogger(__name__)

async def generate_and_send_alert(alert_prompt: AlertPrompt, sourced_document: SourcedData, db: AsyncSession) -> NewsEvent:
    
    if alert_prompt.llm_model == "llama3.1":
        generated_response = await get_ollama_alert_generation(
            sourced_document.content,
            alert_prompt.payload_format,
            sourced_document.source_url
        )
    elif alert_prompt.llm_model == "gemini-2.0-flash":
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
        document_id=sourced_document.id,
        alert_prompt_id=alert_prompt.id,
        triggered_at=datetime.now(),
        output=generated_response.output,
        tags=generated_response.tags,
        source_url=sourced_document.source_url,
        structured_data=generated_response.structured_data,
        
    )

    exception = send_alert_event(llm_generation_result, db)
    
    await save_alert_event(llm_generation_result, generated_response, exception, db)
    await save_document(sourced_document, db)
    await register_credit_usage(alert_prompt, generated_response, db)
    
    return llm_generation_result

def send_alert_event(alert_event: NewsEvent, db: AsyncSession):
    
    stmt = select(AlertPrompt).where(AlertPrompt.id == alert_event.alert_prompt_id)
    result = db.execute(stmt)
    alert_prompt = result.scalar_one_or_none()
    
    try:
        #TODO: add retries or backoff
        with httpx.Client() as client:
            if alert_prompt.http_method == "POST":
                response = client.post(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
            elif alert_prompt.http_method == "PUT":
                response = client.put(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
            elif alert_prompt.http_method == "PATCH":
                response = client.patch(alert_prompt.http_url, json=alert_event.structured_data, headers=alert_prompt.http_headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {alert_prompt.http_method}")
            
            if response.status_code >= 400:
                logger.error(f"Alert webhook failed with status {response.status_code}: {response.text}")
                return str(f"{response.status_code}: {response.text}")
            else:
                return None
            
    except httpx.TimeoutException as e:
        logger.error(f"Timeout while sending alert to {alert_prompt.http_url}: {str(e)}")
        return str(e)
    except httpx.ConnectError as e:
        logger.error(f"Connection error while sending alert to {alert_prompt.http_url}: {str(e)}")
        return str(e)
    except httpx.RequestError as e:
        logger.error(f"Request error while sending alert to {alert_prompt.http_url}: {str(e)}")
        return str(e)
    except Exception as e:
        logger.error(f"Unexpected error while sending alert to {alert_prompt.http_url}: {str(e)}")
        return str(e)

async def save_alert_event(alert_event: NewsEvent, generated_response: LLMGenerationFormat, exception: str, db: AsyncSession) -> AlertEvent:
    alert_event_db = AlertEvent(
        id=alert_event.id,
        alert_prompt_id=alert_event.alert_prompt_id,
        scraped_data_id=alert_event.scraped_data_id,
        triggered_at=alert_event.triggered_at,
        output=generated_response.output,   #TODO: WRONG. It's tokens and prices
        tags=generated_response.tags,
        structured_data=generated_response.structured_data,
        exception=exception
    )
    db.add(alert_event_db)
    await db.commit()

async def save_document(sourced_document: SourcedData, db: AsyncSession):
    if sourced_document.agent_controller_id is None:
        monitored_data_db = MonitoredData(
            id=sourced_document.id,
            source=sourced_document.source,
            name=sourced_document.name,
            content=sourced_document.content,
            content_embedding=sourced_document.content_embedding,
            monitored_datetime=sourced_document.retrieved_datetime,
        )
        db.add(monitored_data_db)
    else:
        user_document_db = UserDocument(
            id=sourced_document.id,
            agent_controller_id=sourced_document.agent_controller_id,
            name=sourced_document.name,
            content=sourced_document.content,
            content_embedding=sourced_document.content_embedding,
            uploaded_datetime=sourced_document.retrieved_datetime,
        )
        db.add(user_document_db)
    await db.commit()

#TODO: unify with get_token_price in llm_validator.py
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
    
    await db.commit()
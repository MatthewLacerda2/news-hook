import os
from dotenv import load_dotenv
from google.genai import Client
from google.genai.types import GenerateContentConfig, EmbedContentConfig
from app.utils.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt
from app.utils.llm_response_formats import LLMValidationFormat, LLMVerificationFormat
import logging
import numpy as np

logger = logging.getLogger(__name__)
load_dotenv()
client = Client(api_key=os.getenv("GEMINI_API_KEY"))

gemini_temperature = 0.0

async def get_gemini_embeddings(text: str) -> np.ndarray:
    response = client.embed(
        model="text-embedding-004",
        input=text,
        config=EmbedContentConfig(
            output_dimensionality=768,      # Optional, dimension of the output vector
        ),
    )
    return np.array(response.embeddings)

async def get_gemini_validation(alert_prompt: str) -> LLMValidationFormat:
    
    full_prompt = get_validation_prompt(alert_prompt)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=full_prompt, config=GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMValidationFormat.model_json_schema(),
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)
    
    json_response = response.text
    
    return LLMValidationFormat.model_validate_json(json_response)

async def get_gemini_verification(alert_prompt: str, document: str) -> LLMVerificationFormat:
    
    print(f"Alert prompt: {alert_prompt}")
    logger.info(f"Alert prompt: {alert_prompt}")
    
    full_prompt = get_verification_prompt(alert_prompt, document)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=full_prompt, config=GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMVerificationFormat.model_json_schema(),
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)

    json_response = response.text
    # Parse the JSON string into our Pydantic model
    return LLMVerificationFormat.model_validate_json(json_response)

async def get_gemini_alert_generation(document: str, payload_format: str, alert_prompt: str) -> str:

    full_prompt = get_generation_prompt(document, payload_format, alert_prompt)
    print(f"Payload format: {payload_format}")
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=full_prompt, config=GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=payload_format,
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)
    
    return response.text

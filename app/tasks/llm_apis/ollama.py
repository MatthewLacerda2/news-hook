from openai import OpenAI
from app.utils.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt
from app.utils.llm_response_formats import LLMValidationFormat, LLMVerificationFormat
import numpy as np
import logging
import json

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama',
)

ollama_temperature = 0.0

async def get_nomic_embeddings(text: str):
    embeddings = client.embeddings.create(
        model="nomic-embed-text",
        input=text,
    )
    
    vector = np.array(embeddings.data[0].embedding)
    norm = np.linalg.norm(vector)
    if norm == 0:
        normalized_vector = vector
    else:
        normalized_vector = vector / norm
    return normalized_vector

async def get_ollama_validation(alert_prompt: str) -> LLMValidationFormat:
    
    full_prompt = get_validation_prompt(alert_prompt)    
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=ollama_temperature,
        stream=False,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
        response_format={"type": "json_object", "schema": LLMValidationFormat.model_json_schema()}
    )
    
    json_response = response.choices[0].message.content
    # Parse the JSON string into our Pydantic model
    return LLMValidationFormat.model_validate_json(json_response)

async def get_ollama_verification(alert_prompt: str, document: str) -> LLMVerificationFormat:
    
    print(f"Alert prompt: {alert_prompt}")
    logger.info(f"Alert prompt: {alert_prompt}")
        
    full_prompt = get_verification_prompt(alert_prompt, document)    
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=ollama_temperature,
        stream=False,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
        response_format={"type": "json_object", "schema": LLMVerificationFormat.model_json_schema()}
    )
    
    json_response = response.choices[0].message.content
    # Parse the JSON string into our Pydantic model
    return LLMVerificationFormat.model_validate_json(json_response)

async def get_ollama_alert_generation(document: str, payload_format: str, alert_prompt: str) -> str:

    full_prompt = get_generation_prompt(document, payload_format, alert_prompt)
    print(f"Payload format: {payload_format}")
    #TODO: tell the AI how to send the structured_data. Do that to Gemini as well
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=ollama_temperature,
        stream=False,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
        response_format={"type": "json_object", "schema": payload_format}
    )
    
    return response.choices[0].message.content
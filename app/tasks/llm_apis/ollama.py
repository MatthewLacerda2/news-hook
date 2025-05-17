from openai import OpenAI
from app.utils.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt
from app.utils.llm_response_formats import LLMValidationFormat, LLMVerificationFormat, LLMGenerationFormat
import numpy as np


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
    
    return response.choices[0].message.content

async def get_ollama_verification(alert_prompt: str, document: str) -> LLMVerificationFormat:
        
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
    
    return response.choices[0].message.content

async def get_ollama_alert_generation(document: str, payload_format: str, source_url: str) -> LLMGenerationFormat:
    
    full_prompt = get_generation_prompt(document, payload_format, source_url)
    #TODO: tell the AI how to send the structured_data. Do that to Gemini as well
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=ollama_temperature,
        stream=False,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
        response_format={"type": "json_object", "schema": LLMGenerationFormat.model_json_schema()}
    )
    
    return response.choices[0].message.content
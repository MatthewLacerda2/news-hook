from dotenv import load_dotenv
import os
from google import genai
from google.genai import types, Client
from google.genai.types import GenerateContentConfig, GenerationConfig
from app.utils.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt
from app.utils.llm_response_formats import LLMValidationFormat, LLMVerificationFormat, LLMGenerationFormat

load_dotenv()
client = Client(api_key=os.getenv("GEMINI_API_KEY"))

gemini_temperature = 0.0

async def get_gemini_validation(alert_prompt: str) -> LLMValidationFormat:
    
    full_prompt = get_validation_prompt(alert_prompt)
    
    response = client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06", contents=full_prompt, config=GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMValidationFormat.model_json_schema(),
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)
    
    return response.text

async def get_gemini_verification(alert_prompt: str, document: str) -> LLMVerificationFormat:
    
    full_prompt = get_verification_prompt(alert_prompt, document)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=full_prompt, generation_config=GenerationConfig(
        response_mime_type='application/json',
        response_schema=LLMVerificationFormat.model_json_schema(),
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)

    return response.text

async def get_gemini_alert_generation(document: str, payload_format: str, source_url: str) -> LLMGenerationFormat:
    
    full_prompt = get_generation_prompt(document, payload_format, source_url)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=full_prompt, generation_config=GenerationConfig(
        response_mime_type='application/json',
        response_schema=LLMGenerationFormat.model_json_schema(),
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)
    
    return response.text
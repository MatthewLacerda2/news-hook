from google import genai
from google.genai import types
from app.utils.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt
from app.utils.llm_response_formats import LLMValidationFormat, LLMVerificationFormat, LLMGenerationFormat

client = genai.Client(api_key="YOUR_API_KEY") #TODO: Add API key

gemini_temperature = 0.0

async def get_gemini_validation(alert_prompt: str) -> LLMValidationFormat:
    
    full_prompt = get_validation_prompt(alert_prompt)
    response = client.models.generate_content(
        model="gemini-2.5-pro", contents=full_prompt, config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMValidationFormat.model_json_schema(),
        temperature=gemini_temperature,
    ),)
    
    return response.text

async def get_gemini_verification(alert_prompt: str, document: str) -> LLMVerificationFormat:
    
    full_prompt = get_verification_prompt(alert_prompt, document)
    response = client.models.generate_content(
        model="gemini-2.5-pro", contents=full_prompt, config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMVerificationFormat.model_json_schema(),
        temperature=gemini_temperature,
    ),)

    return response.text

async def get_gemini_alert_generation(document: str, payload_format: str, source_url: str) -> LLMGenerationFormat:
    
    full_prompt = get_generation_prompt(document, payload_format, source_url)
    response = client.models.generate_content(
        model="gemini-2.5-pro", contents=full_prompt, config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMGenerationFormat.model_json_schema(),
        temperature=gemini_temperature,
    ),)
    
    return response.text
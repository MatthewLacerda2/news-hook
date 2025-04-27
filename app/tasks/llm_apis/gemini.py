from google import genai
from google.genai import types
from app.utils.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt
from app.utils.llm_response_formats import LLMValidationFormat, LLMVerificationFormat, LLMGenerationFormat

client = genai.Client(api_key="YOUR_API_KEY") #TODO: Add API key

async def get_gemini_validation(alert_prompt: str, alert_parsed_intent: str) -> LLMValidationFormat:
    
    full_prompt = get_validation_prompt(alert_prompt, alert_parsed_intent)
    response = client.models.generate_content(
        model="gemini-2.0-flash", temperature=0.5, contents=full_prompt, config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMValidationFormat,
    ),)
    
    return response.text

async def get_gemini_verification(alert_prompt: str, alert_parsed_intent: str, document: str) -> LLMVerificationFormat:
    
    full_prompt = get_verification_prompt(alert_prompt, alert_parsed_intent, document)
    response = client.models.generate_content(
        model="gemini-2.0-flash", temperature=0.5, contents=full_prompt, config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMVerificationFormat,
    ),)

    return response.text

async def get_gemini_alert_generation(alert_parsed_intent: str, document: str, example_response: str) -> LLMGenerationFormat:
    
    full_prompt = get_generation_prompt(alert_parsed_intent, document, example_response)
    response = client.models.generate_content(
        model="gemini-2.0-flash", temperature=0.5, contents=full_prompt, config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMGenerationFormat,
    ),)
    
    return response.text
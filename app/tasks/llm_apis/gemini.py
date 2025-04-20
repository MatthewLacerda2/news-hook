from google import genai
from app.tasks.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt

client = genai.Client(api_key="YOUR_API_KEY")

def get_gemini_validation(alert_prompt: str, alert_parsed_intent: str):    
    
    full_prompt = get_validation_prompt(alert_prompt, alert_parsed_intent)
    response = client.models.generate_content(
        model="gemini-2.0-flash", temperature=0.5, contents=full_prompt
    )
    
    return response.text

def get_gemini_verification(alert_prompt: str, alert_parsed_intent: str, document: str):
    
    full_prompt = get_verification_prompt(alert_prompt, alert_parsed_intent, document)
    response = client.models.generate_content(
        model="gemini-2.0-flash", temperature=0.5, contents=full_prompt
    )

    return response.text

def get_gemini_alert_generation(alert_parsed_intent: str, document: str, example_response: str):
    
    full_prompt = get_generation_prompt(alert_parsed_intent, document, example_response)
    response = client.models.generate_content(
        model="gemini-2.0-flash", temperature=0.5, contents=full_prompt
    )
    
    return response.text
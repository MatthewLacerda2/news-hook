from openai import OpenAI
from app.tasks.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt

client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
)

def get_nomic_embeddings(text: str):
    embeddings = client.embeddings.create(
        model="nomic-embed-text",
        input=text,
    )
    return embeddings

def get_ollama_validation(alert_prompt: str, alert_parsed_intent: str):
    
    full_prompt = get_validation_prompt(alert_prompt, alert_parsed_intent)    
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=0.5,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
    )
    
    return response.choices[0].message.content

def get_ollama_verification(alert_prompt: str, alert_parsed_intent: str, document: str):
        
    full_prompt = get_verification_prompt(alert_prompt, alert_parsed_intent, document)    
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=0.5,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
    )
    
    return response.choices[0].message.content

def get_ollama_alert_generation(alert_parsed_intent: str, document: str, example_response: str):
    
    full_prompt = get_generation_prompt(alert_parsed_intent, document, example_response)    
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=0.5,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
    )
    
    return response.choices[0].message.content
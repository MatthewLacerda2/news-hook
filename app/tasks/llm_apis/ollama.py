from openai import OpenAI
from datetime import datetime
from app.tasks.prompts import validation_prompt, verification_prompt, alert_verification_prompt

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

def get_ollama_validation(text: str, alert_prompt: str, alert_parsed_intent: str, document: str):    
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    full_prompt = validation_prompt.format(
        alert_prompt=alert_prompt,
        alert_parsed_intent=alert_parsed_intent,
        current_date_time=current_date_time
    )
    
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=0.5,
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": text}
        ],
    )
    return response.choices[0].message.content

def get_ollama_verification(text: str, alert_prompt: str, alert_parsed_intent: str, document: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    full_prompt = verification_prompt.format(
        alert_prompt=alert_prompt,
        alert_parsed_intent=alert_parsed_intent,
        document=document,
        current_date_time=current_date_time
    )
    
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=0.5,
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": text}
        ],
    )
    return response.choices[0].message.content

def get_ollama_alert_verification(text: str, alert_parsed_intent: str, document: str, example_response: str):
    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    full_prompt = alert_verification_prompt.format(
        alert_parsed_intent=alert_parsed_intent,
        document=document,
        example_response=example_response,
        current_date_time=current_date_time
    )
    
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=0.5,
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": text}
        ],
    )
    
    return response.choices[0].message.content



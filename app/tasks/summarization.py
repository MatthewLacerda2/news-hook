from app.utils.prompts import get_summarization_prompt
from app.utils.count_tokens import count_tokens
from openai import OpenAI

client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama',
)

ollama_temperature = 0.0
chunk_size = 2048

def is_document_too_large(document: str, llm_model: str) -> bool:
    """
    Check if the document could use summarization.
    """
    token_count = count_tokens(document, llm_model)
    return token_count > chunk_size

async def get_summarization_by_ollama(document: str) -> str:
    """
    Get a summarization of the content using ollama.
    """
    response = client.chat.completions.create(
        model="llama3.1",
        temperature=ollama_temperature,
        stream=False,
        messages=[
            {"role": "user", "content": get_summarization_prompt(document)},
        ]
    )    
    return response.choices[0].message.content

async def get_summarization_by_gemini(document: str) -> str:    
    response = client.models.generate_content(
        model="gemini-2.5-pro-preview-05-06", contents=get_summarization_prompt(document)
    )    
    return response.text

from app.tasks.llm_apis.gemini import get_client

def count_tokens(text: str, model: str) -> int:
    
    client = get_client()
    
    total_tokens = client.models.count_tokens(
        model=model,
        contents=text
    )
    
    return total_tokens
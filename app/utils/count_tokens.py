from google import genai

def count_tokens(text: str, model: str) -> int:
    
    client = genai.Client()
    
    total_tokens = client.models.count_tokens(
        model=model,
        contents=text
    )
    
    return total_tokens
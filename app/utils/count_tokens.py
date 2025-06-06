from app.tasks.llm_apis.gemini import get_client
import logging
import tiktoken

logger = logging.getLogger(__name__)

def count_tokens(text: str, model: str) -> int:
    
    #client = get_client()    
    #total_tokens = client.models.count_tokens(
    #    model=model,
    #    contents=text
    #)    
    #return total_tokens.total_tokens

    #TODO: this is an approximation
    #We were using the official package, but that's an API call, and it's taking too much time
    #We should optimize later, including async calls
    model_to_encoding = {
        "llama3.1": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-4": "cl100k_base",
        "gemini-2.0-flash": "cl100k_base",
        "gemini-2.5-pro-preview-05-06": "cl100k_base",
    }
    encoding_name = model_to_encoding.get(model, "cl100k_base")
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))
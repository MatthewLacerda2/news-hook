import tiktoken

def count_tokens(text: str, model: str) -> int:
    model_to_encoding = {
        "llama3.1": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-4": "cl100k_base",
        "gemini-2.5-pro-preview-05-06": "cl100k_base",
    }
    encoding_name = model_to_encoding.get(model, "cl100k_base")
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))
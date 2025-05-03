from app.utils.llm_response_formats import LLMValidationFormat
from app.schemas.alert_prompt import AlertPromptCreateRequestBase
from app.tasks.llm_apis.ollama import get_ollama_validation
from app.tasks.llm_apis.gemini import get_gemini_validation
import tiktoken
from app.models.llm_models import LLMModel
import json

def count_tokens(text: str, model: str) -> int:
    model_to_encoding = {
        "llama3.1": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "gpt-4": "cl100k_base",
        "gemini-2.5-pro": "cl100k_base",
    }
    encoding_name = model_to_encoding.get(model, "cl100k_base")
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))

async def get_llm_validation(alert_request: AlertPromptCreateRequestBase, llm_model: str) -> LLMValidationFormat:
    """
    Validate the alert request using LLM
    """
    
    # Choose LLM based on model name
    validation_result: LLMValidationFormat
    if llm_model == "llama3.1":
        validation_result = await get_ollama_validation(
            alert_request.prompt,
            alert_request.parsed_intent,
        )
    elif llm_model == "gemini-2.5-pro":
        validation_result = await get_gemini_validation(
            alert_request.prompt,
            alert_request.parsed_intent,
        )
    else:
        msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
        print(f"Unsupported LLM model: {llm_model}\n{msg}")
        raise ValueError(f"Unsupported LLM model: {llm_model}")
    
    if isinstance(validation_result, str):
        validation_result = LLMValidationFormat(**json.loads(validation_result))    
    
    return validation_result

def get_llm_validation_price(alert_request: AlertPromptCreateRequestBase, validation_result: LLMValidationFormat, llm_model: LLMModel) -> float:
    """
    Get the price of the LLM validation
    """
    
    input_token_count = count_tokens(alert_request.prompt, llm_model.model_name) + count_tokens(str(alert_request.parsed_intent), llm_model.model_name)
    output_token_count = count_tokens(str(validation_result.output_intent), llm_model.model_name)
    
    input_price = input_token_count * (llm_model.input_token_price/1000000)
    output_price = output_token_count * (llm_model.output_token_price/1000000)
    
    return input_price, output_price

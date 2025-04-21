from app.utils.llm_response_formats import LLMValidationFormat
from app.schemas.alert_prompt import AlertPromptCreateRequestBase
from app.tasks.llm_apis.ollama import get_ollama_validation
from app.tasks.llm_apis.gemini import get_gemini_validation
import tiktoken
from app.models.llm_models import LLMModel
from app.tasks.llm_apis.ollama import get_nomic_embeddings
from app.models.llm_validation import LLMValidation
from datetime import datetime

async def llm_validation(alert_request: AlertPromptCreateRequestBase, llm_model: str) -> LLMValidationFormat:
    """
    Validate the alert request using LLM
    """
    
    # Choose LLM based on model name
    validation_result: LLMValidationFormat
    if llm_model == "llama3.1":
        validation_result = get_ollama_validation(
            alert_request.prompt,
            alert_request.parsed_intent,
        )
    elif llm_model == "gemini":
        validation_result = get_gemini_validation(
            alert_request.prompt,
            alert_request.parsed_intent,
        )
    else:
        msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
        print(f"Unsupported LLM model: {llm_model}\n{msg}")
        raise ValueError(f"Unsupported LLM model: {llm_model}")
    
    return validation_result

def get_llm_validation_price(alert_request: AlertPromptCreateRequestBase, validation_result: LLMValidationFormat, llm_model: LLMModel) -> float:
    """
    Get the price of the LLM validation
    """
    
    input_token_count = tiktoken.count_tokens(alert_request.prompt) + tiktoken.count_tokens(str(alert_request.parsed_intent))
    output_token_count = tiktoken.count_tokens(validation_result)
    
    input_price = input_token_count * (llm_model.input_token_price/1000000)
    output_price = output_token_count * (llm_model.output_token_price/1000000)
    
    return input_price, output_price
    
    

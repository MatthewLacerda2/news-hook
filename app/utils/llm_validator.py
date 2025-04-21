from app.utils.llm_response_formats import LLMValidationFormat
from app.schemas.alert_prompt import AlertPromptCreateRequestBase
from app.tasks.llm_apis.ollama import get_ollama_validation
from app.tasks.llm_apis.gemini import get_gemini_validation


def llm_validation(alert_request: AlertPromptCreateRequestBase, llm_model: str) -> LLMValidationFormat:
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
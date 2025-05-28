from app.utils.llm_response_formats import LLMValidationFormat
from app.schemas.alert_prompt import AlertPromptCreateRequestBase
from app.tasks.llm_apis.gemini import get_gemini_validation
from app.utils.count_tokens import count_tokens
from app.models.llm_models import LLMModel
import json

async def get_llm_validation(alert_request: AlertPromptCreateRequestBase, llm_model: str) -> LLMValidationFormat:
    """
    Validate the alert request using LLM
    """
    
    validation_result: LLMValidationFormat
    if llm_model == "gemini-2.0-flash":
        validation_result = await get_gemini_validation(
            alert_request.prompt,
        )
    else:
        msg = "This shouldn't even be possible, as the LLM model is checked before the alert is created"
        print(f"Unsupported LLM model: {llm_model}\n{msg}")
        raise ValueError(f"Unsupported LLM model: {llm_model}")
    
    if isinstance(validation_result, str):
        validation_result = LLMValidationFormat(**json.loads(validation_result))    
    
    return validation_result

#TODO: this should be (input, output, llm_model)
def get_token_price(alert_request: AlertPromptCreateRequestBase, validation_result: LLMValidationFormat, llm_model: LLMModel) -> float:
    """
    Get the price of the LLM validation
    """
    
    input_token_count = count_tokens(alert_request.prompt, llm_model.model_name)
    output_token_count = count_tokens(str(validation_result.reason), llm_model.model_name)
    
    input_price = input_token_count * (llm_model.input_token_price/1000000)
    output_price = output_token_count * (llm_model.output_token_price/1000000)
    
    return input_price, output_price

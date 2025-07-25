import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.genai import Client
from google.genai.types import GenerateContentConfig, EmbedContentConfig, ContentEmbedding
from app.utils.prompts import get_validation_prompt, get_verification_prompt, get_generation_prompt
from app.utils.llm_response_formats import LLMValidationFormat, LLMVerificationFormat
import logging
import numpy as np
from app.utils.env import NUM_EMBEDDING_DIMENSIONS, FLAGSHIP_MODEL
from app.core.config import settings
from app.utils.env import GOOGLE_PROJECT_ID
from google.genai import types

logger = logging.getLogger(__name__)
load_dotenv()

def get_client():
    #credentials = Credentials(
        #token=None,  # Token is automatically fetched using refresh token
        #refresh_token=settings.GOOGLE_REFRESH_TOKEN,
        #client_id=settings.GOOGLE_CLIENT_ID,
        #client_secret=settings.GOOGLE_CLIENT_SECRET,
        #token_uri='https://oauth2.googleapis.com/token',  # This is the standard Google OAuth2 token endpoint
    #)
    
    return Client(
        vertexai=True,
        project=GOOGLE_PROJECT_ID,
        location="global",
        #credentials=credentials    #TODO: uncomment this when you figure the values out. They were fine until they weren't
    )

gemini_temperature = 0.0

def get_gemini_embeddings(text: str, task_type: str) -> np.ndarray:
    
    client = get_client()
    
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=EmbedContentConfig(
            output_dimensionality=NUM_EMBEDDING_DIMENSIONS,
            task_type=task_type,
        ),
    )
    # Extract the actual float values from the ContentEmbedding object
    embedding_values = response.embeddings[0].values
    return np.array(embedding_values, dtype=np.float32)

def get_gemini_validation(alert_prompt: str) -> LLMValidationFormat:
    
    client = get_client()
    full_prompt = get_validation_prompt(alert_prompt)
    
    response = client.models.generate_content(
        model=FLAGSHIP_MODEL, contents=full_prompt, config=GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMValidationFormat.model_json_schema(),
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)
    
    json_response = response.text
    
    return LLMValidationFormat.model_validate_json(json_response)

def get_gemini_verification(alert_prompt: str, document: str, llm_model: str) -> LLMVerificationFormat:
    
    client = get_client()
    full_prompt = get_verification_prompt(alert_prompt, document)
    
    response = client.models.generate_content(
        model=llm_model, contents=full_prompt, config=GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=LLMVerificationFormat.model_json_schema(),
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)

    json_response = response.text
    
    # Parse the JSON string into our Pydantic model
    return LLMVerificationFormat.model_validate_json(json_response)


def get_gemini_alert_generation(document: str, is_json: bool, alert_prompt: str, llm_model: str) -> str:
    
    client = get_client()
    full_prompt = get_generation_prompt(document, alert_prompt)
    
    response_type = 'application/json' if is_json else 'text/plain'
        
    response = client.models.generate_content(
        model=llm_model, contents=full_prompt, config=GenerateContentConfig(
        response_mime_type=response_type,
        temperature=gemini_temperature,
        automatic_function_calling={"disable": True}
    ),)
    
    return response.text

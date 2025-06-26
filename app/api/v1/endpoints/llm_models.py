from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy import select
import logging
from app.schemas.llm_models import LLMModelListResponse
from app.models.llm_models import LLMModel
from app.core.database import get_db

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/", response_model=LLMModelListResponse)
async def list_llm_models(
    db: AsyncSession = Depends(get_db)
):
    """
    List all active LLM models.
    """
    query = select(LLMModel).where(LLMModel.is_active == True).order_by(
        LLMModel.output_token_price.asc(),
        LLMModel.input_token_price.asc()
    )
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    return LLMModelListResponse(items=models)

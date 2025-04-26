from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy import select

from app.schemas.llm_models import LLMModelListResponse
from app.models.llm_models import LLMModel
from app.core.database import get_db

router = APIRouter()

@router.get("/", response_model=LLMModelListResponse)
async def list_llm_models(
    actives_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    List available LLM models.
    If actives_only is True (default), only return active models.
    If actives_only is False, return all models.
    """
    query = select(LLMModel)
    if actives_only:
        query = query.where(LLMModel.is_active == True)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    return LLMModelListResponse(items=models)

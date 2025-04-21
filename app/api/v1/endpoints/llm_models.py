from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.schemas.llm_models import LLMModelListResponse
from app.models.llm_models import LLMModel
from app.core.database import get_db

router = APIRouter()

@router.get("/llm-models", response_model=LLMModelListResponse)
async def list_llm_models(
    actives_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    List available LLM models.
    If actives_only is True (default), only return active models.
    If actives_only is False, return all models.
    """
    query = db.query(LLMModel)
    if actives_only:
        query = query.filter(LLMModel.is_active == True)
    
    models = await db.execute(query)
    models = models.scalars().all()
    
    return LLMModelListResponse(items=models)

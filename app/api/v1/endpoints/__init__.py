from fastapi import APIRouter
from app.api.v1.endpoints import alert, auth, llm_models

router = APIRouter()
router.include_router(alert.router, prefix="/alert", tags=["alert"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(llm_models.router, prefix="/llm-models", tags=["llm_models"])
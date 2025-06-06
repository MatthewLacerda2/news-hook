from fastapi import APIRouter
from app.api.v1.endpoints import alert, auth, llm_models, user_document, event
from app.core.rate_limiter import limiter

router = APIRouter()

router.dependency_overrides = {
    "rate_limit": limiter.limit("60/minute")
}

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(alert.router, prefix="/alerts", tags=["alerts"])
router.include_router(llm_models.router, prefix="/llm-models", tags=["llm_models"])
router.include_router(user_document.router, prefix="/user_documents", tags=["user_documents"])
router.include_router(event.router, prefix="/event", tags=["event"])
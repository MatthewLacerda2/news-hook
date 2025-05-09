from fastapi import APIRouter
from app.api.v1.endpoints import alert, auth, llm_models, document, notification
from app.core.rate_limiter import limiter

router = APIRouter()

# Add rate limit to all routes in this router
router.dependency_overrides = {
    "rate_limit": limiter.limit("60/minute")
}

# Include routers with their prefixes
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(alert.router, prefix="/alerts", tags=["alerts"])
router.include_router(document.router, prefix="/documents", tags=["documents"])
router.include_router(llm_models.router, prefix="/llm-models", tags=["llm_models"])
router.include_router(notification.router, prefix="/notifications", tags=["notifications"])

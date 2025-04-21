from fastapi import APIRouter, Depends
from app.api.v1.endpoints import alert, auth
from slowapi import Limiter

router = APIRouter()
router.include_router(alert.router, prefix="/alert", tags=["alert"], dependencies=[Depends(Limiter.limit("50/minute")),])
router.include_router(auth.router, prefix="/auth", tags=["auth"], dependencies=[Depends(Limiter.limit("20/minute")),])
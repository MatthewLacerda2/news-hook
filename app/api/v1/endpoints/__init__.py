from fastapi import APIRouter
from app.api.v1.endpoints import alert, auth

router = APIRouter()
router.include_router(alert.router, prefix="/alert", tags=["alert"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
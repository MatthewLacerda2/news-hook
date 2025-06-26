import logging
from fastapi import APIRouter
from fastapi import status

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=str,
    description="Create a new alert for monitoring"
)
async def create_alert():
    pass

@router.patch(
    "/{alert_id}/cancel",
    status_code=status.HTTP_200_OK,
    response_model=str,
    description="Mark an alert as CANCELLED. We do not 'delete' the alert") #Not for billing purposes, but for metrics
async def cancel_alert():
    pass

@router.get(
    "/",
    response_model=list[str],
    description="List all active alerts"
)
async def list_alerts():
    pass
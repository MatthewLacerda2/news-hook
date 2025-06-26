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
    
    #Verify if alert is duplicated
    #get llm validation
    #save the validation
    #if validation approves, create the alert
    #async task for saving the embedding
    #reply saying if accepted or denied
    
    pass

@router.patch(
    "/{alert_id}/cancel",
    status_code=status.HTTP_200_OK,
    response_model=str,
    description="Mark an alert as CANCELLED. We do not 'delete' the alert") #Not for billing purposes, but for metrics
async def cancel_alert():
    
    #check if alert with that id and owned by that user is in the db
    #if not, return 404
    #if it is, update the status to cancelled
    #reply back
    
    pass

@router.get(
    "/",
    response_model=list[str],
    description="List all active alerts"
)
async def list_alerts():
    
    #just check the db for all active alerts owned by that user
    pass
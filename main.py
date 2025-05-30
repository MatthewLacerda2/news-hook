import functions_framework
from app.tasks.manual_document import handle_manual_document
from app.tasks.docling_scraping import handle_periodic_check_http
import asyncio

@functions_framework.http
def process_document_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
    Returns:
        JSON response with status or error
    """
    # Cloud Functions need to wrap async code in a sync function
    return asyncio.run(handle_manual_document(request))

@functions_framework.http
def periodic_check_http(request):
    """HTTP Cloud Function for periodic checks.
    Args:
        request (flask.Request): The request object.
    Returns:
        JSON response with status or next interval
    """
    return asyncio.run(handle_periodic_check_http(request))
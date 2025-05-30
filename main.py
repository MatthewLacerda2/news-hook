import functions_framework
from app.tasks.manual_document import handle_manual_document
import asyncio

@functions_framework.http
def process_document_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
    Returns:
        JSON response with status or error
    """
    return asyncio.run(handle_manual_document(request))
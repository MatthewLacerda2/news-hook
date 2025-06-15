from app.core.database import AsyncSessionLocal
from app.tasks.process_manual_document import process_manual_document

async def handle_manual_document(request):
    """
    Google Cloud Function to handle manual document processing
    
    Expected request body:
    {
        "name": "Document Title",
        "content": "Document content in markdown",
    }
    """
    try:
        request_json = request.get_json()
        
        db = AsyncSessionLocal()
        try:
            await process_manual_document(
                name=request_json["name"],
                content=request_json["content"],
                db=db
            )
            return {"status": "success"}, 201
        finally:
            await db.close()
            
    except Exception as e:
        return {"error": str(e)}, 500
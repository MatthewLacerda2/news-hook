from fastapi import FastAPI
from .core.database import engine, Base

# Create FastAPI app instance
app = FastAPI(
    title="News Hook API",
    description="API for monitoring and alerting on news and content updates",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to News Hook API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

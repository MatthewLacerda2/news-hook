from fastapi import FastAPI, Request
from app.api.v1.endpoints import router as api_v1_router

app = FastAPI(
    title="News Hook API",
    description="API for monitoring and alerting on news and content updates",
    version="1.0.0"
)


app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root(request: Request):
    return {"message": "Welcome to News Hook API"}

@app.get("/health")
async def health_check(request: Request):
    return {"status": "healthy"}
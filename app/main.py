from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.v1.endpoints import router as api_v1_router

app = FastAPI(
    title="News Hook API",
    description="API for monitoring and alerting on news and content updates",
    version="1.0.0"
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
@limiter.limit("50/minute")
async def root(request: Request):
    return {"message": "Welcome to News Hook API"}

@app.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    return {"status": "healthy"}
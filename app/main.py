import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_v1_router
from app.core.logging_middleware import LoggingMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="News Hook API",
    description="API for monitoring and alerting on news and content updates",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(LoggingMiddleware)
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root(request: Request):
    return {"message": "Welcome to News Hook API"}

@app.get("/health")
async def health_check(request: Request):
    return {"status": "healthy"}
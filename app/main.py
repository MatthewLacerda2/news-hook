import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_v1_router
from app.core.logging_middleware import LoggingMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="News Hook API",
    description="API for monitoring and alerting on news and content updates",
    version="1.0.0"
)

@app.on_event("startup")
async def run_migrations():
    try:
        logger.info("Running database migrations...")
        alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Database migrations completed successfully")
        logger.debug(f"Migration output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running migrations: {e.stderr}")
        # Don't raise the error - let the app start even if migrations fail
        # This allows for manual intervention if needed
    except Exception as e:
        logger.error(f"Unexpected error running migrations: {str(e)}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

limiter = Limiter(key_func=get_remote_address)
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
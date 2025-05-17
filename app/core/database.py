from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

#This is how it's done now
ASYNC_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI.replace('postgresql://', 'postgresql+asyncpg://')

# Create SQLAlchemy async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10
)

# SessionLocal will be used to create database sessions
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

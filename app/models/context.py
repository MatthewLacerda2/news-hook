from sqlalchemy import Column, String, DateTime
from app.models.base import Base
import uuid
from datetime import datetime

class Context(Base):
    __tablename__ = "contexts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    expires_at = Column(DateTime, nullable=True)
    
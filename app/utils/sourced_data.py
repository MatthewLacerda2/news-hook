from app.models.base import Base
from app.models.monitored_data import DataSource
from datetime import datetime
from uuid import UUID
from pgvector.sqlalchemy import Vector
import uuid

class SourcedData(Base):

    id : UUID
    scraped_datetime : datetime
    source : DataSource
    source_url : str
    content : str
    content_embedding : Vector
    
    def __init__(self, source: DataSource, source_url: str, content: str, content_embedding: Vector):
        self.id = uuid.uuid4()
        self.scraped_datetime = datetime.now()
        self.source = source
        self.source_url = source_url
        self.content = content
        self.content_embedding = content_embedding
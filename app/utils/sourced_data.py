from app.models.monitored_data import DataSource
from datetime import datetime
from pgvector.sqlalchemy import Vector
import uuid
from dataclasses import dataclass

@dataclass
class SourcedData:
    id: str
    agent_controller_id: str | None
    retrieved_datetime: datetime
    source: DataSource
    source_url: str
    source_id: str
    document_id: str
    name: str
    content: str
    content_embedding: Vector    
    def __init__(self, source: DataSource, source_url: str, content: str, content_embedding: Vector, name: str, agent_controller_id: str = None):
        self.id = str(uuid.uuid4())
        self.retrieved_datetime = datetime.now()
        self.source = source
        self.source_url = source_url
        self.content = content
        self.content_embedding = content_embedding
        self.name = name
        self.agent_controller_id = agent_controller_id
        self.source_id = ""
        self.document_id = ""

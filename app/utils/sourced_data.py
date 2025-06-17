from app.models.monitored_data import DataSource
from datetime import datetime
from pgvector.sqlalchemy import Vector
from dataclasses import dataclass

@dataclass
class SourcedData:
    id: str
    agent_controller_id: str | None
    retrieved_datetime: datetime
    source: DataSource
    source_id: str | None
    document_id: str
    name: str
    content: str
    content_embedding: Vector
    
    def __init__(self, id: str, source: DataSource, content: str, content_embedding: Vector, name: str, agent_controller_id: str = None, document_id: str = ""):
        self.id = id
        self.retrieved_datetime = datetime.now()
        self.source = source
        self.content = content
        self.content_embedding = content_embedding
        self.name = name
        self.agent_controller_id = agent_controller_id
        self.source_id = ""
        self.document_id = document_id

import uuid
from datetime import datetime
from typing import Dict

class AlertTrigger:
    id: uuid.UUID
    alert_prompt_id: uuid.UUID
    scraped_data_id: uuid.UUID
    triggered_at: datetime
    response: Dict

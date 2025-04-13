import uuid
from datetime import datetime

class AlertTrigger:
    id: uuid.UUID
    alert_id: uuid.UUID  # reference to Alert
    scraped_data_id: uuid.UUID  # reference to ScrapedData
    triggered_at: datetime
    notification_sent: bool

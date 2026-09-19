from dataclasses import dataclass
from datetime import datetime


@dataclass
class EventContract:
    event_id: str
    event_type: str
    timestamp: datetime
    source: str
    version: str = "1.0"
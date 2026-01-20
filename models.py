from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CardEvent:
    card_number: str
    reader_name: str
    timestamp: datetime
    raw_data: str
    event_type: str = "Access Granted"

    def __str__(self):
        return f"[{self.timestamp}] Card: {self.card_number} @ {self.reader_name} ({self.event_type})"

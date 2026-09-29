# Models/CalendarEvent.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CalendarEvent:
    title: str
    start: datetime
    end: datetime
    source: str  
# logic/Models/CalendarEvent.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CalendarEvent:
    title: str
    start: datetime
    end: datetime
    source: str
    id: str = ""
    location: str = ""
    description: str = ""
    all_day: bool = False
    calendar: str = ""  # friendly calendar name, e.g. "work" / "school" / "personal"
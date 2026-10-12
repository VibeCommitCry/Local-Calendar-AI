# logic/Models/CalendarFilter.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CalendarFilter:
    query: str = ""                 
    start: datetime | None = None 
    end: datetime | None = None    
    max_results: int = 20
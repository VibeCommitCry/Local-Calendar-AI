# Models/EmailMessage.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EmailMessage:
    id: str
    sender: str
    subject: str
    received: datetime
    snippet: str   # short preview text from Gmail
    source: str    # "gmail", later maybe "outlook"
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EmailMessage:
    id: str
    sender: str
    subject: str
    received: datetime
    snippet: str
    source: str
    body: str = "" 
# logic/Models/EmailFilter.py
from dataclasses import dataclass

@dataclass
class EmailFilter:
    query: str = ""          # free text / provider search syntax
    sender: str = ""
    subject: str = ""
    label: str = ""
    unread_only: bool = False
    newer_than_days: int = 0  # 0 = no limit
    max_results: int = 10
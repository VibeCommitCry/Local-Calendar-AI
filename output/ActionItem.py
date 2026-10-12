from datetime import date, time
from typing import Literal

from pydantic import BaseModel


class ActionItem(BaseModel):
    title: str
    due_date: date | None = None  # model writes "YYYY-MM-DD", pydantic parses it into a real date
    due_time: time | None = None  # model writes "HH:MM"
    priority: Literal["low", "medium", "high"]  # anything else fails validation
    source_id: str
    quote: str  # exact sentence from the email, so a human can check the item


class EmailActionItems(BaseModel):
    email_id: str
    summary: str
    items: list[ActionItem]


class CalendarEventActionItems(BaseModel):
    event_id: str
    summary: str
    items: list[ActionItem]

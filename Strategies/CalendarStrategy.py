# Strategies/CalendarStrategy.py
from abc import ABC, abstractmethod
from datetime import datetime

from Models.CalendarEvent import CalendarEvent
from Models.CalendarFilter import CalendarFilter


class CalendarStrategy(ABC):
    source: str  # unique name, e.g. "google"

    # READ
    @abstractmethod
    def read_events(self, filters: CalendarFilter) -> list[CalendarEvent]:
        """Return events in the filter's time window, sorted by start."""

    @abstractmethod
    def get_event(self, event_id: str) -> CalendarEvent:
        """Fetch one event including its description."""

    # CREATE / UPDATE / DELETE
    @abstractmethod
    def create_event(self, title: str, start: datetime, end: datetime,
                     location: str = "", description: str = "") -> CalendarEvent:
        """Create an event."""

    @abstractmethod
    def update_event(self, event_id: str, **changes) -> CalendarEvent:
        """Update an event."""

    @abstractmethod
    def delete_event(self, event_id: str) -> None:
        """Delete an event."""
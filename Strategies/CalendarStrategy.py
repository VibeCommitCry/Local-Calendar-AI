from abc import ABC, abstractmethod
from Models.CalendarEvent import CalendarEvent

class CalendarStrategy(ABC):
    @abstractmethod
    def collect_calendar(self) -> list[CalendarEvent]:
        """Return this source's events as normalized CalendarEvents."""
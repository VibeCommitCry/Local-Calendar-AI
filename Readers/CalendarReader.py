# CalendarReader.py
from Models.CalendarEvent import CalendarEvent
from Strategies.CalendarStrategy import CalendarStrategy
from Strategies.CalendarGoogle import CalendarGoogle
# from Strategies.CalendarMicrosoft import CalendarMicrosoft


class CalendarReader:

    def collect_calendars(self) -> list[CalendarEvent]:
        """Run every CalendarStrategy implementation and merge the results."""
        events: list[CalendarEvent] = []
        for strategy_cls in CalendarStrategy.__subclasses__():
            events.extend(self.collect_calendar(strategy_cls()))

        return sorted(events, key=lambda e: e.start)

    def collect_calendar(self, strategy: CalendarStrategy) -> list[CalendarEvent]:
        return strategy.collect_calendar()

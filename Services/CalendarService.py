# Services/CalendarService.py
from datetime import date, datetime, time, timedelta

from Models.CalendarEvent import CalendarEvent
from Models.CalendarFilter import CalendarFilter
from Strategies.CalendarStrategy import CalendarStrategy
from Strategies.CalendarGoogle import CalendarGoogle  # import so it registers as a subclass
from settings import LOCAL_TZ


class CalendarService:

    def __init__(self):
        self._strategies = {cls.source: cls() for cls in CalendarStrategy.__subclasses__()}

    def _strategy(self, source: str) -> CalendarStrategy:
        if source not in self._strategies:
            raise ValueError(f"Unknown calendar source: {source}")
        return self._strategies[source]

    # ---------- CRUD ----------
    def read_events(self, filters: CalendarFilter | None = None) -> list[CalendarEvent]:
        filters = filters or CalendarFilter()
        events: list[CalendarEvent] = []
        for strategy in self._strategies.values():
            events.extend(strategy.read_events(filters))
        events.sort(key=lambda e: e.start)
        return events[: filters.max_results]

    def get_event(self, event_id: str, calendar: str = "", source: str = "google") -> CalendarEvent:
        return self._strategy(source).get_event(event_id, calendar)

    def create_event(self, title, start, end, location="", description="",
                     calendar="", source="google"):
        return self._strategy(source).create_event(
            title, start, end, location, description, calendar
        )

    def update_event(self, event_id: str, source: str = "google", **changes):
        return self._strategy(source).update_event(event_id, **changes)

    def delete_event(self, event_id: str, source: str = "google"):
        return self._strategy(source).delete_event(event_id)

    # ---------- free time ----------
    def find_free_time(
        self,
        duration_minutes: int = 60,
        days: int = 7,
        day_start: time = time(9, 0),
        day_end: time = time(17, 0),
        include_weekends: bool = False,
        max_slots: int = 15,
    ) -> list[tuple[datetime, datetime]]:
        now = datetime.now(LOCAL_TZ)
        first_day = now.date()
        window_start = datetime.combine(first_day, time.min, tzinfo=LOCAL_TZ)
        window_end = datetime.combine(first_day + timedelta(days=days), time.min, tzinfo=LOCAL_TZ)

        events = self.read_events(
            CalendarFilter(start=window_start, end=window_end, max_results=250)
        )
        # All-day events (birthdays, "Payday") don't block time
        busy = sorted(
            ((e.start, e.end) for e in events if not e.all_day), key=lambda b: b[0]
        )

        needed = timedelta(minutes=duration_minutes)
        slots: list[tuple[datetime, datetime]] = []

        for offset in range(days):
            day: date = first_day + timedelta(days=offset)
            if not include_weekends and day.weekday() >= 5:
                continue

            cursor = max(datetime.combine(day, day_start, tzinfo=LOCAL_TZ), now)
            limit = datetime.combine(day, day_end, tzinfo=LOCAL_TZ)
            if cursor >= limit:
                continue

            for b_start, b_end in busy:
                if b_end <= cursor:
                    continue
                if b_start >= limit:
                    break
                gap_end = min(b_start, limit)
                if gap_end - cursor >= needed:
                    slots.append((cursor, gap_end))
                cursor = max(cursor, b_end)
                if cursor >= limit:
                    break

            if cursor < limit and limit - cursor >= needed:
                slots.append((cursor, limit))

            if len(slots) >= max_slots:
                break

        return slots[:max_slots]
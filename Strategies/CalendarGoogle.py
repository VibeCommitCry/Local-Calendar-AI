# Strategies/CalendarGoogle.py
import datetime as dt

from googleapiclient.discovery import build

from Auth.GoogleAuth import get_google_credentials
from Models.CalendarEvent import CalendarEvent
from Models.CalendarFilter import CalendarFilter
from Strategies.CalendarStrategy import CalendarStrategy
from settings import LOCAL_TZ


class CalendarGoogle(CalendarStrategy):
    source = "google"
    CALENDAR_ID = "primary"

    def __init__(self):
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build("calendar", "v3", credentials=get_google_credentials())
        return self._service

    # ---------- READ ----------
    def read_events(self, filters: CalendarFilter) -> list[CalendarEvent]:
        start = filters.start or dt.datetime.now(LOCAL_TZ)
        end = filters.end or (start + dt.timedelta(days=14))

        params = dict(
            calendarId=self.CALENDAR_ID,
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            maxResults=filters.max_results,
            singleEvents=True,       # expands recurring events
            orderBy="startTime",
        )
        if filters.query:
            params["q"] = filters.query

        result = self.service.events().list(**params).execute()
        return [self._to_event(raw) for raw in result.get("items", [])]

    def get_event(self, event_id: str) -> CalendarEvent:
        raw = (
            self.service.events()
            .get(calendarId=self.CALENDAR_ID, eventId=event_id)
            .execute()
        )
        return self._to_event(raw)

    # ---------- CREATE / UPDATE / DELETE (later build steps) ----------
    def create_event(self, title, start, end, location="", description=""):
        raise NotImplementedError("Creating events comes in build step 4")

    def update_event(self, event_id, **changes):
        raise NotImplementedError("Not implemented yet")

    def delete_event(self, event_id):
        raise NotImplementedError("Not implemented yet")

    # ---------- helpers ----------
    @staticmethod
    def _parse(value: dict) -> dt.datetime:
        # Timed events have "dateTime" (with offset); all-day events only have "date"
        if "dateTime" in value:
            return dt.datetime.fromisoformat(value["dateTime"])
        d = dt.date.fromisoformat(value["date"])
        return dt.datetime(d.year, d.month, d.day, tzinfo=LOCAL_TZ)

    def _to_event(self, raw: dict) -> CalendarEvent:
        return CalendarEvent(
            id=raw["id"],
            title=raw.get("summary", "(no title)"),
            start=self._parse(raw["start"]),
            end=self._parse(raw["end"]),
            source=self.source,
            location=raw.get("location", ""),
            description=raw.get("description", ""),
            all_day="date" in raw["start"],
        )
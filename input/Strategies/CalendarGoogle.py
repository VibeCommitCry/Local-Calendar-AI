# Strategies/CalendarGoogle.py
import datetime as dt

from googleapiclient.discovery import build

from Auth.GoogleAuth import get_google_credentials
from Models.CalendarEvent import CalendarEvent
from Models.CalendarFilter import CalendarFilter
from Strategies.CalendarStrategy import CalendarStrategy
from settings import CALENDAR_IDS, LOCAL_TZ, WRITABLE_CALENDARS


class CalendarGoogle(CalendarStrategy):
    source = "google"

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
        events: list[CalendarEvent] = []

        for name, calendar_id in CALENDAR_IDS.items():
            params = dict(
                calendarId=calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                maxResults=filters.max_results,
                singleEvents=True,       # expands recurring events
                orderBy="startTime",
            )
            if filters.query:
                params["q"] = filters.query

            result = self.service.events().list(**params).execute()
            events.extend(self._to_event(raw, name) for raw in result.get("items", []))

        return events

    def get_event(self, event_id: str, calendar: str = "") -> CalendarEvent:
        raw = (
            self.service.events()
            .get(calendarId=self._calendar_id(calendar), eventId=event_id)
            .execute()
        )
        return self._to_event(raw, calendar)

    # ---------- CREATE / UPDATE / DELETE ----------
    def create_event(self, title, start, end, location="", description="", calendar=""):
        if calendar not in WRITABLE_CALENDARS:
            raise ValueError(
                f"Can't add events to calendar '{calendar}'. "
                f"Use one of: {', '.join(WRITABLE_CALENDARS)}"
            )

        if end is None:
            # All-day event: Google wants dates, with an exclusive end day
            day = start.astimezone(LOCAL_TZ).date()
            when = {
                "start": {"date": day.isoformat()},
                "end": {"date": (day + dt.timedelta(days=1)).isoformat()},
            }
        else:
            when = {
                "start": {"dateTime": start.isoformat()},
                "end": {"dateTime": end.isoformat()},
            }

        body = {"summary": title, **when}
        if location:
            body["location"] = location
        if description:
            body["description"] = description

        raw = (
            self.service.events()
            .insert(calendarId=self._calendar_id(calendar), body=body)
            .execute()
        )
        return self._to_event(raw, calendar)

    def update_event(self, event_id, **changes):
        raise NotImplementedError("Not implemented yet")

    def delete_event(self, event_id):
        raise NotImplementedError("Not implemented yet")

    # ---------- helpers ----------
    @staticmethod
    def _calendar_id(calendar: str) -> str:
        if calendar not in CALENDAR_IDS:
            raise ValueError(
                f"Unknown calendar '{calendar}'. Use one of: {', '.join(CALENDAR_IDS)}"
            )
        return CALENDAR_IDS[calendar]

    @staticmethod
    def _parse(value: dict) -> dt.datetime:
        # Timed events have "dateTime" (with offset); all-day events only have "date"
        if "dateTime" in value:
            return dt.datetime.fromisoformat(value["dateTime"])
        d = dt.date.fromisoformat(value["date"])
        return dt.datetime(d.year, d.month, d.day, tzinfo=LOCAL_TZ)

    def _to_event(self, raw: dict, calendar: str) -> CalendarEvent:
        return CalendarEvent(
            id=raw["id"],
            title=raw.get("summary", "(no title)"),
            start=self._parse(raw["start"]),
            end=self._parse(raw["end"]),
            source=self.source,
            location=raw.get("location", ""),
            description=raw.get("description", ""),
            all_day="date" in raw["start"],
            calendar=calendar,
        )
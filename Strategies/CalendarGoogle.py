# Strategies/CalendarGoogle.py
import datetime
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build

from Auth.GoogleAuth import get_google_credentials
from Models.CalendarEvent import CalendarEvent
from Strategies.CalendarStrategy import CalendarStrategy

LOCAL_TZ = ZoneInfo("Europe/Amsterdam")


class CalendarGoogle(CalendarStrategy):

    def collect_calendar(self, max_results: int = 10) -> list[CalendarEvent]:
        return [self._to_event(raw) for raw in self.get_upcoming_events(max_results)]

    def get_upcoming_events(self, max_results: int = 10) -> list[dict]:
        service = build("calendar", "v3", credentials=get_google_credentials())
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])

    @staticmethod
    def _parse(value: dict) -> datetime.datetime:
        # Timed events have "dateTime" (with offset); all-day events only have "date"
        if "dateTime" in value:
            return datetime.datetime.fromisoformat(value["dateTime"])
        # All-day: a plain date, treat it as midnight local time
        d = datetime.date.fromisoformat(value["date"])
        return datetime.datetime(d.year, d.month, d.day, tzinfo=LOCAL_TZ)

    def _to_event(self, raw: dict) -> CalendarEvent:
        return CalendarEvent(
            title=raw.get("summary", "(no title)"),
            start=self._parse(raw["start"]),
            end=self._parse(raw["end"]),
            source="google",
        )


if __name__ == "__main__":
    for e in CalendarGoogle().collect_calendar():
        print(e.start, "-", e.title)

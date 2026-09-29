# Strategies/CalendarGoogle.py
import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from Models.CalendarEvent import CalendarEvent
from Strategies.CalendarStrategy import CalendarStrategy

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class CalendarGoogle(CalendarStrategy):

    def collect_calendar(self, max_results: int = 10) -> list[CalendarEvent]:
        return [self._to_event(raw) for raw in self.get_upcoming_events(max_results)]

    def get_credentials(self) -> Credentials:
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    def get_upcoming_events(self, max_results: int = 10) -> list[dict]:
        service = build("calendar", "v3", credentials=self.get_credentials())
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
        
        raw = value.get("dateTime") or value["date"]
        return datetime.datetime.fromisoformat(raw)

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
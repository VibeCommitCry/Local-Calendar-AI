# Strategies/CalendarMicrosoft.py
import os
from datetime import datetime, timedelta, timezone

import msal
import requests
from dotenv import load_dotenv

from Models.CalendarEvent import CalendarEvent
from Strategies.CalendarStrategy import CalendarStrategy

load_dotenv()

CLIENT_ID = os.environ["MS_CLIENT_ID"]
AUTHORITY = f"https://login.microsoftonline.com/{os.environ['MS_TENANT_ID']}"
SCOPES = ["Calendars.Read"]
CACHE_FILE = "ms_token_cache.json"


class CalendarMicrosoft(CalendarStrategy):

    def collect_calendar(self, days_ahead: int = 14) -> list[CalendarEvent]:
        token = self.get_token()
        now = datetime.now(timezone.utc)
        params = {
            "startDateTime": now.isoformat(),
            "endDateTime": (now + timedelta(days=days_ahead)).isoformat(),
            "$orderby": "start/dateTime",
            "$top": 50,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Prefer": 'outlook.timezone="UTC"',
        }
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me/calendarView",
            params=params, headers=headers, timeout=15,
        )
        response.raise_for_status()
        return [self._to_event(raw) for raw in response.json()["value"]]

    def get_token(self) -> str:
        cache = msal.SerializableTokenCache()
        if os.path.exists(CACHE_FILE):
            cache.deserialize(open(CACHE_FILE).read())

        app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

        result = None
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if not result:
            result = app.acquire_token_interactive(SCOPES)  

        if cache.has_state_changed:
            with open(CACHE_FILE, "w") as f:
                f.write(cache.serialize())

        if "access_token" not in result:
            raise RuntimeError(result.get("error_description", "Microsoft login failed"))
        return result["access_token"]

    @staticmethod
    def _parse(value: dict) -> datetime:
        # Graph returns e.g. "2026-09-30T08:00:00.0000000" (7 fractional digits, UTC)
        raw = value["dateTime"].split(".")[0]
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)

    def _to_event(self, raw: dict) -> CalendarEvent:
        return CalendarEvent(
            title=raw.get("subject") or "(no title)",
            start=self._parse(raw["start"]),
            end=self._parse(raw["end"]),
            source="microsoft",
        )
# scripts/list_calendars.py
"""One-off: print the id, name and access role of every calendar in the account.
Run from the repo root: python -m scripts.list_calendars"""

from googleapiclient.discovery import build

from logic.Auth.GoogleAuth import get_google_credentials

service = build("calendar", "v3", credentials=get_google_credentials())
for c in service.calendarList().list().execute().get("items", []):
    print(f"{c['accessRole']:<8} | {c['summary']:<30} | {c['id']}")

# logic/Auth/GoogleAuth.py
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.app.created",  # create/manage secondary calendars + their events
    "https://www.googleapis.com/auth/calendar.calendars",  # view/edit calendar properties, create secondary calendars
    "https://www.googleapis.com/auth/calendar.events.owned",  # create/edit/delete events on calendars you own
    "https://www.googleapis.com/auth/gmail.readonly",  # read emails
    "https://www.googleapis.com/auth/gmail.drafts.create",  # create draft emails (not send)
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "https://www.googleapis.com/auth/calendar.events.readonly",
]


def get_google_credentials() -> Credentials:
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

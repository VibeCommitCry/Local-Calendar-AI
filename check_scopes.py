# check_scopes.py  (run from the project root)
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

print("Working directory:", os.getcwd())
print("Client ID:", flow.client_config["client_id"])
print("Granted scopes:", creds.granted_scopes)
# settings.py  (project root)
# Copy this file to settings.py (git-ignored) and fill in your own calendar ids.
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Amsterdam")

# Google calendars the agent uses: friendly name -> calendar id.
# Ids and access roles come from `python -m scripts.list_calendars`.
CALENDAR_IDS = {
    "work": "primary",
    "school": "CALENDAR_ID@group.calendar.google.com",
    "personal": "CALENDAR_ID@group.calendar.google.com",
}

# Calendars with accessRole "owner"; the school calendar is read-only
WRITABLE_CALENDARS = ["work", "personal"]

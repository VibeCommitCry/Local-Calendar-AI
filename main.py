
from Readers.CalendarReader import CalendarReader

if __name__ == "__main__":
    for e in CalendarReader().collect_calendars():
        print(e.start, "-", e.title)
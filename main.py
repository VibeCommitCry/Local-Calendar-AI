from Readers.CalendarReader import CalendarReader
from Readers.EmailReader import EmailReader

if __name__ == "__main__":
    print("-------- Calendar ----------")
    for e in CalendarReader().collect_calendars():
        print(e.start, "-", e.title)
    print("-------- Calendar ----------")
    
    print("--------          ----------")
    
    print("-------- Email ----------")

    for m in EmailReader().collect_emails():
        print(m.received, "|", m.sender, "|", m.subject)
    print("-------- Email ----------")

from Services.EmailService import EmailService
from Models.EmailFilter import EmailFilter

from Services.CalendarService import CalendarService

for m in EmailService().read_emails(EmailFilter(unread_only=True)):
    print(m.received, "|", m.sender, "|", m.subject)


for e in CalendarService().read_events():
    print(e.start, "-", e.title)

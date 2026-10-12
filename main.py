from logic.Services.EmailService import EmailService
from logic.Models.EmailFilter import EmailFilter

from logic.Services.CalendarService import CalendarService

for m in EmailService().read_emails(EmailFilter(unread_only=True)):
    print(m.received, "|", m.sender, "|", m.subject)


for e in CalendarService().read_events():
    print(e.start, "-", e.title)

# Readers/EmailReader.py
from Models.EmailMessage import EmailMessage
from Strategies.EmailStrategy import EmailStrategy
from Strategies.EmailGmail import EmailGmail


class EmailReader:

    def collect_emails(self) -> list[EmailMessage]:
        emails: list[EmailMessage] = []
        for strategy_cls in EmailStrategy.__subclasses__():
            emails.extend(self.collect_email(strategy_cls()))
        return sorted(emails, key=lambda e: e.received, reverse=True)

    def collect_email(self, strategy: EmailStrategy) -> list[EmailMessage]:
        return strategy.collect_emails()

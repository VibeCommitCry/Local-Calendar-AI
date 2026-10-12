# Services/EmailService.py
from Models.EmailFilter import EmailFilter
from Models.EmailMessage import EmailMessage
from Strategies.EmailStrategy import EmailStrategy
from Strategies.EmailGmail import EmailGmail  # import so it registers as a subclass


class EmailService:

    def __init__(self):
        self._strategies = {cls.source: cls() for cls in EmailStrategy.__subclasses__()}

    def _strategy(self, source: str) -> EmailStrategy:
        if source not in self._strategies:
            raise ValueError(f"Unknown email source: {source}")
        return self._strategies[source]

    def read_emails(self, filters: EmailFilter | None = None) -> list[EmailMessage]:
        filters = filters or EmailFilter()
        emails: list[EmailMessage] = []
        for strategy in self._strategies.values():
            emails.extend(strategy.read_emails(filters))
        emails.sort(key=lambda e: e.received, reverse=True)
        return emails[: filters.max_results]

    def get_email(self, email_id: str, source: str = "gmail") -> EmailMessage:
        return self._strategy(source).get_email(email_id)

    def create_email(self, to: str, subject: str, body: str, source: str = "gmail"):
        return self._strategy(source).create_email(to, subject, body)

    def update_email(self, email_id: str, source: str = "gmail", **changes):
        return self._strategy(source).update_email(email_id, **changes)

    def delete_email(self, email_id: str, source: str = "gmail"):
        return self._strategy(source).delete_email(email_id)
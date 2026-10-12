# input/Strategies/EmailStrategy.py
from abc import ABC, abstractmethod

from logic.Models.EmailFilter import EmailFilter
from logic.Models.EmailMessage import EmailMessage


class EmailStrategy(ABC):
    source: str  # unique name, e.g. "gmail"

    # READ
    @abstractmethod
    def read_emails(self, filters: EmailFilter) -> list[EmailMessage]:
        """Search emails (metadata + snippet only)."""

    @abstractmethod
    def get_email(self, email_id: str) -> EmailMessage:
        """Fetch one email including its full body."""

    # CREATE / UPDATE / DELETE
    @abstractmethod
    def create_email(self, to: str, subject: str, body: str) -> EmailMessage:
        """Create a draft."""

    @abstractmethod
    def update_email(self, email_id: str, **changes) -> EmailMessage:
        """Update an email (labels, read state, draft text)."""

    @abstractmethod
    def delete_email(self, email_id: str) -> None:
        """Delete or trash an email."""
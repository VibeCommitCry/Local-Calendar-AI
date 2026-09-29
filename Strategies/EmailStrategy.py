# Strategies/EmailStrategy.py
from abc import ABC, abstractmethod
from Models.EmailMessage import EmailMessage

class EmailStrategy(ABC):
    @abstractmethod
    def collect_emails(self) -> list[EmailMessage]:
        """Return this source's emails as normalized EmailMessages."""
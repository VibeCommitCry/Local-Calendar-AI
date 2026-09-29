# Strategies/EmailGmail.py
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build

from Auth.GoogleAuth import get_google_credentials
from Models.EmailMessage import EmailMessage
from Strategies.EmailStrategy import EmailStrategy


class EmailGmail(EmailStrategy):

    def collect_emails(self, query: str = "is:unread", max_results: int = 10) -> list[EmailMessage]:
        service = build("gmail", "v1", credentials=get_google_credentials())

        # The list call only returns message IDs, so each message is fetched separately
        listing = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        emails = []
        for ref in listing.get("messages", []):
            raw = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=ref["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
            emails.append(self._to_email(raw))
        return emails

    def _to_email(self, raw: dict) -> EmailMessage:
        headers = {h["name"]: h["value"] for h in raw["payload"]["headers"]}
        return EmailMessage(
            id=raw["id"],
            sender=headers.get("From", "(unknown)"),
            subject=headers.get("Subject", "(no subject)"),
            received=parsedate_to_datetime(headers["Date"]),
            snippet=raw.get("snippet", ""),
            source="gmail",
        )
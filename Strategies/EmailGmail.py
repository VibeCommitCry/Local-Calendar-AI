# Strategies/EmailGmail.py
import base64
import html
import re
from datetime import datetime, timezone

from googleapiclient.discovery import build

from Auth.GoogleAuth import get_google_credentials
from Models.EmailFilter import EmailFilter
from Models.EmailMessage import EmailMessage
from Strategies.EmailStrategy import EmailStrategy


class EmailGmail(EmailStrategy):
    source = "gmail"

    def __init__(self):
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build("gmail", "v1", credentials=get_google_credentials())
        return self._service

    # ---------- READ ----------
    def read_emails(self, filters: EmailFilter) -> list[EmailMessage]:
        listing = (
            self.service.users()
            .messages()
            .list(userId="me", q=self._build_query(filters), maxResults=filters.max_results)
            .execute()
        )
        emails = []
        for ref in listing.get("messages", []):
            raw = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=ref["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject"],
                )
                .execute()
            )
            emails.append(self._to_email(raw))
        return emails

    def get_email(self, email_id: str) -> EmailMessage:
        raw = (
            self.service.users()
            .messages()
            .get(userId="me", id=email_id, format="full")
            .execute()
        )
        return self._to_email(raw, include_body=True)

    # ---------- CREATE / UPDATE / DELETE (later build steps) ----------
    def create_email(self, to: str, subject: str, body: str) -> EmailMessage:
        raise NotImplementedError("Drafting comes in build step 3")

    def update_email(self, email_id: str, **changes) -> EmailMessage:
        raise NotImplementedError("Not implemented yet")

    def delete_email(self, email_id: str) -> None:
        raise NotImplementedError("Not implemented yet")

    # ---------- helpers ----------
    @staticmethod
    def _build_query(f: EmailFilter) -> str:
        parts = []
        if f.unread_only:
            parts.append("is:unread")
        if f.sender:
            parts.append(f"from:({f.sender})")
        if f.subject:
            parts.append(f"subject:({f.subject})")
        if f.label:
            parts.append(f"label:{f.label}")
        if f.newer_than_days > 0:
            parts.append(f"newer_than:{f.newer_than_days}d")
        if f.query:
            parts.append(f.query)
        return " ".join(parts)

    def _to_email(self, raw: dict, include_body: bool = False) -> EmailMessage:
        headers = {h["name"].lower(): h["value"] for h in raw["payload"].get("headers", [])}
        return EmailMessage(
            id=raw["id"],
            sender=headers.get("from", "(unknown)"),
            subject=headers.get("subject", "(no subject)"),
            # internalDate is epoch milliseconds, always present, no header parsing needed
            received=datetime.fromtimestamp(int(raw["internalDate"]) / 1000, tz=timezone.utc),
            snippet=raw.get("snippet", ""),
            source=self.source,
            body=self._extract_body(raw["payload"]) if include_body else "",
        )

    def _extract_body(self, payload: dict) -> str:
        plain, html_parts = [], []

        def decode(data: str) -> str:
            data += "=" * (-len(data) % 4)  # Gmail strips base64 padding
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        def walk(part: dict) -> None:
            mime = part.get("mimeType", "")
            data = part.get("body", {}).get("data")
            if data and mime == "text/plain":
                plain.append(decode(data))
            elif data and mime == "text/html":
                html_parts.append(decode(data))
            for sub in part.get("parts", []):
                walk(sub)

        walk(payload)
        if plain:
            return "\n".join(plain).strip()
        if html_parts:
            return self._html_to_text("\n".join(html_parts))
        return ""

    @staticmethod
    def _html_to_text(raw_html: str) -> str:
        text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw_html)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()
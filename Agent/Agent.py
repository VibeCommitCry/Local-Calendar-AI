# agent.py
import ollama
from datetime import datetime
from Readers.CalendarReader import CalendarReader
from Readers.EmailReader import EmailReader

MODEL = "qwen2.5:14b"


def get_calendar_events() -> str:
    """Get the user's upcoming calendar events."""
    events = CalendarReader().collect_calendars()
    return (
        "\n".join(f"{e.start:%a %d %b %H:%M} - {e.title}" for e in events)
        or "No events."
    )


def get_unread_emails() -> str:
    """Get the user's recent unread emails (sender, subject, preview)."""
    mails = EmailReader().collect_emails()
    return (
        "\n".join(f"From {m.sender} | {m.subject} | {m.snippet}" for m in mails)
        or "No unread email."
    )


available = {f.__name__: f for f in (get_calendar_events, get_unread_emails)}


def ask(question: str) -> str:
    today = datetime.now().strftime("%A %d %B %Y, %H:%M")
    messages = [
        {
            "role": "system",
            "content": (
                f"You are a personal assistant. Today is {today}. "
                "Use the tools to answer. Be concise."
            ),
        },
        {"role": "user", "content": question},
    ]
    while True:
        response = ollama.chat(
            model=MODEL, messages=messages, tools=list(available.values())
        )
        messages.append(response.message)
        if not response.message.tool_calls:
            return response.message.content
        for call in response.message.tool_calls:
            name = call.function.name
            try:
                result = (
                    available[name]() if name in available else f"Unknown tool: {name}"
                )
            except Exception as e:
                result = f"Tool {name} failed: {e}"
            messages.append({"role": "tool", "tool_name": name, "content": result})


if __name__ == "__main__":
    print(
        ask(
            "Give me a briefing for today: the date, my schedule, and any emails that need attention."
        )
    )

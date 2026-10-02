# Agent/Agent.py
import ollama
from datetime import datetime

from Agent.agent_tools import TOOLS, run_tool

MODEL = "qwen2.5:14b"
MAX_HISTORY = 30  # keep the context from growing forever


def system_message() -> dict:
    today = datetime.now().strftime("%A %d %B %Y, %H:%M")
    return {
        "role": "system",
        "content": (
            f"You are a personal assistant. Today is {today}. "
            "Use the tools to answer. Be concise. "
            "Only report what the tools return; don't guess what an event is about."
            "To dig into an email, first call search_emails, then read_email with the id. "
            "For the calendar, use search_calendar_events (or find_free_time to find open slots). "
        ),
    }


def ask(messages: list, question: str) -> str:
    """Add the question to the shared history, run the tool loop, return the answer."""
    messages.append({"role": "user", "content": question})

    while True:
        response = ollama.chat(
            model=MODEL, messages=messages, tools=list(TOOLS.values())
        )
        messages.append(response.message)

        if not response.message.tool_calls:
            return response.message.content

        for call in response.message.tool_calls:
            name = call.function.name
            result = run_tool(name, call.function.arguments)
            messages.append({"role": "tool", "tool_name": name, "content": result})


def trim(messages: list) -> None:
    """Keep the system message plus the most recent MAX_HISTORY messages."""
    if len(messages) > MAX_HISTORY + 1:
        del messages[1:-MAX_HISTORY]
        # don't start the history on an orphaned tool result
        while len(messages) > 1 and (
            (
                messages[1].get("role")
                if isinstance(messages[1], dict)
                else messages[1].role
            )
            == "tool"
        ):
            del messages[1]


def main() -> None:
    messages = [system_message()]
    print("Assistant ready. Type 'exit' to quit, 'reset' to clear the conversation.\n")

    while True:
        try:
            question = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            break
        if question.lower() == "reset":
            messages = [system_message()]
            print("Conversation cleared.\n")
            continue

        try:
            print(f"\n{ask(messages, question)}\n")
        except Exception as e:
            print(f"\n[error] {e}\n")

        trim(messages)


if __name__ == "__main__":
    main()

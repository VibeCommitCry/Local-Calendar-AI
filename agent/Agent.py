# agent/Agent.py
import ollama
from datetime import datetime, timedelta
from pathlib import Path

from agent.agent_tools import TOOLS, memory_prompt, run_tool

MODEL = "qwen2.5:3b"
MAX_TOOL_ROUNDS = 5  # stop a confused model from looping forever
MAX_HISTORY = 30  # keep the context from growing forever
IDENTITY_DIR = Path(__file__).parent / "Identity"


def load_identity() -> str:
    """Build the system prompt from the files in agent/Identity/."""
    read = lambda name: (IDENTITY_DIR / name).read_text(encoding="utf-8").strip()

    now = datetime.now()
    upcoming = "\n".join(f"  {now + timedelta(days=i):%A %Y-%m-%d}" for i in range(8))
    # str.replace, not str.format: a stray brace in the markdown shouldn't crash startup
    agents = (
        read("AGENTS.md")
        .replace("{now}", f"{now:%A %d %B %Y, %H:%M}")
        .replace("{upcoming}", upcoming)
    )

    return "\n\n".join([read("SOUL.md"), agents, read("TOOLS.md"), memory_prompt()])


def system_message() -> dict:
    return {"role": "system", "content": load_identity()}


def ask(messages: list, question: str) -> str:
    """Add the question to the shared history, run the tool loop, return the answer."""
    messages.append({"role": "user", "content": question})

    for _ in range(MAX_TOOL_ROUNDS):
        response = ollama.chat(
            model=MODEL, messages=messages, tools=list(TOOLS.values())
        )
        messages.append(response.message)

        if not response.message.tool_calls:
            return response.message.content

        for call in response.message.tool_calls:
            name = call.function.name
            result = run_tool(name, call.function.arguments)
            print(f"  [tool] {name}({dict(call.function.arguments or {})}) -> {result[:80]!r}")
            messages.append({"role": "tool", "tool_name": name, "content": result})
            if name == "remember":
                messages[0] = system_message()  # pick up the new fact this session

    return "I couldn't finish that request. Try asking in a simpler way."


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

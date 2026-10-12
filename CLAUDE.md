# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A personal assistant that runs a local LLM (Ollama, `qwen2.5:3b`) with tool-calling over the user's Google Calendar, Gmail, and (in progress) Microsoft calendar. Python, no package structure — modules are imported from the repo root, so run everything from the root directory.

## Commands

- Install: `pip install -r requirements.txt` (note: the file is UTF-16 encoded; also needs `python-dotenv`, which isn't listed)
- Run the chat agent: `python -m agent.Agent` (requires a running Ollama server with the model pulled: `ollama pull qwen2.5:3b`)
- Smoke test of the services without the LLM: `python main.py`
- `check_scopes.py` is a helper for inspecting the Google token scopes.
- `python -m scripts.list_calendars` prints each Google calendar's access role, name and id (use it to fill `CALENDAR_IDS`).
- `tests/test_google_calender_api.py` is currently empty; there is no test runner configured.

## Secrets / local files

- Google OAuth: `credentials.json` (client secret) and `token.json` (generated on first run via browser flow, in the CWD). Scopes in [logic/Auth/GoogleAuth.py](logic/Auth/GoogleAuth.py) allow creating/editing events on owned calendars, reading gmail and creating drafts (not sending); changing `SCOPES` requires deleting `token.json` to re-consent.
- Microsoft: `MS_CLIENT_ID` / `MS_TENANT_ID` from `.env` (see `.env.example`); token cache in `ms_token_cache.json`. [input/Strategies/CalendarMicrosoft.py](input/Strategies/CalendarMicrosoft.py) reads these with `os.environ[...]` at import time, so importing it without `.env` raises `KeyError`.
- Timezone is hard-coded in [settings.py](settings.py) (`LOCAL_TZ`, Europe/Amsterdam) and used for all calendar windowing and display.
- [settings.py](settings.py) also holds `CALENDAR_IDS` (friendly name → Google calendar id: `work` = Jumbo werkdagen/primary, `school` = Avans, `personal`) and `WRITABLE_CALENDARS` (`work`, `personal`). The school calendar is read-only by design: always read, never write.

## Architecture

Top-level folders: `agent/` (chat agent + tools), `input/` (provider fetching, i.e. what goes into the chat), `logic/` (dataclass models, auth, services), `output/` (pydantic validation of model output; `output/extract_email.py` is run with `python -m output.extract_email`, results go to the git-ignored `output/results/`). `settings.py`, `main.py`, `scripts/` and `tests/` stay in the root.

Layered, with a Strategy pattern per data provider:

- **logic/Models/** — plain dataclasses (`CalendarEvent`, `CalendarFilter`, `EmailMessage`, `EmailFilter`). Filters are the provider-neutral query objects.
- **input/Strategies/** — one abstract base per domain (`CalendarStrategy`, `EmailStrategy`) with provider implementations (`CalendarGoogle`, `CalendarMicrosoft`, `EmailGmail`). Each strategy has a `source` name.
- **logic/Services/** — `CalendarService` / `EmailService` are the current high-level API: filter-based `read_events`/`get_event`/CRUD, plus `find_free_time` (computes gaps from non-all-day events). Strategies are discovered via `CalendarStrategy.__subclasses__()`, so **a strategy only registers if its module has been imported** (see the "import so it registers" line in `CalendarService.py`). `get_event` and CRUD default to `source="google"`.
- **Multiple Google calendars** — `CalendarGoogle.read_events` loops over every entry in `CALENDAR_IDS` and tags each `CalendarEvent.calendar` with the friendly name; `get_event`/`create_event` take that name. `create_event` refuses calendars not in `WRITABLE_CALENDARS`. Event ids are only unique per calendar, so the tools expose them as `"<calendar>:<id>"` (built in `_fmt_event`, split again in `get_calendar_event`).
- **agent/** — [agent/agent_tools.py](agent/agent_tools.py) holds the tools; [agent/Agent.py](agent/Agent.py) is the Ollama chat loop (history trimmed to the last 30 messages, loops until the model stops requesting tool calls).

### System prompt (`agent/Identity/`)

`system_message()` in [agent/Agent.py](agent/Agent.py) joins four files: `SOUL.md` (personality), `AGENTS.md` (rules + style; `{now}`/`{upcoming}` are substituted with `str.replace`), `TOOLS.md` (one-line overview, the docstrings stay the real tool schema) and `MEMORY.md`. `MEMORY.md` is written by the `remember` tool (lines `- [level] fact`, level 1–10, duplicates merged; lines without a level count as 5), not edited by hand. `memory_prompt()` in `agent_tools.py` groups it into "Always follow" (8–10), "Keep in mind" (4–7) and "Small details" (1–3) for the prompt; after a `remember` call `ask()` rebuilds `messages[0]` so the fact is used in the same session. Add a line to `TOOLS.md` when adding a tool.

### Adding an agent tool

Decorate a function with `@tool` in `agent_tools.py`. The function's signature and Google-style docstring (`Args:`) are passed straight to Ollama as the tool schema, so the docstring is the model's instructions. Tools return strings. `run_tool` drops arguments the function doesn't accept and converts exceptions into error strings. Untrusted content (email bodies, event descriptions) is wrapped in "untrusted data" markers to resist prompt injection — keep that for any new tool that returns external text.

The module-level service objects are `emails` and `calendar_service` (not `calendar`, which is a tool parameter name).

### Write tools need confirmation

`create_calendar_event` is two-step: with `confirmed=False` (default) it returns a "NOT CREATED YET" overview for the model to show the user; only a second call with `confirmed=True` writes. It also refuses to guess a date (only `today`/`tomorrow` or an explicit `start_date`), because `_resolve_when` falls back to "now". Follow the same pattern for any new tool that changes real data (update/delete events, drafts).

### Known in-progress state

`CalendarMicrosoft` still implements the old `collect_calendar` method and doesn't implement the abstract methods of the new `CalendarStrategy` (`read_events`, `get_event`, create/update/delete), and `CalendarService` doesn't import it. Finishing the Microsoft migration means implementing that interface and importing the module in `CalendarService.py`.

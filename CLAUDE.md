# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A personal assistant that runs a local LLM (Ollama, `qwen2.5:3b`) with tool-calling over the user's Google Calendar, Gmail, and (in progress) Microsoft calendar. Python, no package structure — modules are imported from the repo root, so run everything from the root directory.

## Commands

- Install: `pip install -r requirements.txt` (note: the file is UTF-16 encoded; also needs `python-dotenv`, which isn't listed)
- Run the chat agent: `python -m Agent.Agent` (requires a running Ollama server with the model pulled: `ollama pull qwen2.5:3b`)
- Smoke test of the services without the LLM: `python main.py`
- `check_scopes.py` is a helper for inspecting the Google token scopes.
- `tests/test_google_calender_api.py` is currently empty; there is no test runner configured.

## Secrets / local files

- Google OAuth: `credentials.json` (client secret) and `token.json` (generated on first run via browser flow, in the CWD). Scopes are read-only (calendar + gmail) in [Auth/GoogleAuth.py](Auth/GoogleAuth.py); changing `SCOPES` requires deleting `token.json` to re-consent.
- Microsoft: `MS_CLIENT_ID` / `MS_TENANT_ID` from `.env` (see `.env.example`); token cache in `ms_token_cache.json`. [Strategies/CalendarMicrosoft.py](Strategies/CalendarMicrosoft.py) reads these with `os.environ[...]` at import time, so importing it without `.env` raises `KeyError`.
- Timezone is hard-coded in [settings.py](settings.py) (`LOCAL_TZ`, Europe/Amsterdam) and used for all calendar windowing and display.

## Architecture

Layered, with a Strategy pattern per data provider:

- **Models/** — plain dataclasses (`CalendarEvent`, `CalendarFilter`, `EmailMessage`, `EmailFilter`). Filters are the provider-neutral query objects.
- **Strategies/** — one abstract base per domain (`CalendarStrategy`, `EmailStrategy`) with provider implementations (`CalendarGoogle`, `CalendarMicrosoft`, `EmailGmail`). Each strategy has a `source` name.
- **Services/** — `CalendarService` / `EmailService` are the current high-level API: filter-based `read_events`/`get_event`/CRUD, plus `find_free_time` (computes gaps from non-all-day events). Strategies are discovered via `CalendarStrategy.__subclasses__()`, so **a strategy only registers if its module has been imported** (see the "import so it registers" line in `CalendarService.py`). `get_event` and CRUD default to `source="google"`.
- **Readers/** — older API (`collect_calendars()` / `collect_emails()`) that merges all strategies. Superseded by Services but still used by the `get_calendar_events` tool.
- **Agent/** — [Agent/agent_tools.py](Agent/agent_tools.py) holds the tools; [Agent/Agent.py](Agent/Agent.py) is the Ollama chat loop (history trimmed to the last 30 messages, loops until the model stops requesting tool calls).

### Adding an agent tool

Decorate a function with `@tool` in `agent_tools.py`. The function's signature and Google-style docstring (`Args:`) are passed straight to Ollama as the tool schema, so the docstring is the model's instructions. Tools return strings. `run_tool` drops arguments the function doesn't accept and converts exceptions into error strings. Untrusted content (email bodies, event descriptions) is wrapped in "untrusted data" markers to resist prompt injection — keep that for any new tool that returns external text.

### Known in-progress state

`CalendarMicrosoft` still implements the old `collect_calendar` method and doesn't implement the abstract methods of the new `CalendarStrategy` (`read_events`, `get_event`, create/update/delete), and `CalendarService` doesn't import it. Finishing the Microsoft migration means implementing that interface and importing the module in `CalendarService.py`.

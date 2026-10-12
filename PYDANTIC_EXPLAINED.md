# Pydantic explained (for this project)

## 1. What is pydantic?

Pydantic lets you describe the shape of your data as a Python class. It then checks any data against that class and turns it into real Python objects.

An LLM returns text. Even if that text looks like JSON, it can have a missing field, a wrong type or a made-up value. Pydantic is the gate between "text from the model" and "data my code can trust".

```python
class ActionItem(BaseModel):
    title: str
    due_date: date | None = None
```

- `ActionItem.model_validate_json('{"title": "Hand in report", "due_date": "2026-10-16"}')` gives an `ActionItem` whose `due_date` is a real `date` object, not a string.
- `... "due_date": "2026-13-45"` raises a `ValidationError`.

## 2. What I added

| File | What it is |
|---|---|
| `Models/ActionItem.py` | The two pydantic models: `ActionItem` and `EmailActionItems` |
| `Extract/extract_email.py` | `extract_action_items(email)`: asks the model, validates, retries once. Running it as a script processes every email in `tests/Samples/Email.json` |
| `.gitignore` | Added `output/`, where the JSON results are saved |

### The models

```
EmailActionItems
├── email_id: str
├── summary: str
└── items: list[ActionItem]
        ├── title: str
        ├── due_date: date | None
        ├── due_time: time | None
        ├── priority: "low" | "medium" | "high"
        ├── source_email_id: str
        └── quote: str
```

## 3. What is checked, and how

There are three layers. Each one catches things the previous layer can't.

### Layer 1: the schema while the model writes (Ollama, `format=`)

- **How:** `EmailActionItems.model_json_schema()` turns the classes into a JSON Schema. It is passed to `ollama.chat(format=...)`. Ollama only lets the model produce tokens that fit that schema.
- **Checks:** the output is valid JSON with the right field names and basic types.
- **Cannot check:** whether the values make sense. This is not pydantic. It happens inside Ollama.

### Layer 2: pydantic validation (`model_validate_json`)

- **How:** `EmailActionItems.model_validate_json(raw_text)` parses the text and checks it against the models.
- **Checks:**
  - The text is valid JSON.
  - No required field is missing (`title`, `priority`, `quote`, ...).
  - Types are right: `title` is a string, `items` is a list.
  - `priority` is exactly `low`, `medium` or `high`.
  - `due_date` is a real calendar date (`"2026-02-30"` fails) and `due_time` is a real time (`"25:99"` fails).
  - It converts strings into `date` and `time` objects, so the date work is done in code and not by the model.
- **Cannot check:** whether a valid value is correct. `2025-10-14` is a perfectly valid date, even if the email says 2026.

### Layer 3: my own checks (`_check_against_email`)

Pydantic only sees the model's JSON, never the email. So I added checks that compare the result with the real email:

- `email_id` and every `source_email_id` must equal the real email id. This stops the model from inventing ids.
- Every `quote` must appear word for word in the email body. If it doesn't, the item was probably invented.

These raise a `ValueError`.

### Still not checked

- A wrong but plausible date (`due_date` that doesn't match the email).
- A wrong priority.
- A missed action item (the model returned fewer items than it should).
- A real quote attached to a wrong title.

These need your judgment, or extra code you add yourself (see section 6).

## 4. When it is checked

```
email
  │
  ▼
build prompt (email body wrapped in "untrusted data" markers)
  │
  ▼
ollama.chat(format=schema)                ← layer 1 (during generation)
  │
  ▼
model_validate_json(reply)                ← layer 2 (right after the reply)
  │
  ▼
_check_against_email(result, email)       ← layer 3 (only if layer 2 passed)
  │
  ├─ OK ──────────────► return the result, save output/<id>.json
  │
  └─ error
       ├─ first time: send the reply + the error back to the model, try ONE more time
       └─ second time: raise RuntimeError (the script prints FAILED and goes on to the next email)
```

Nothing unvalidated is ever returned or saved.

## 5. Why it is built this way

- **Why validate at all?** A model's output is untrusted input. Without validation a bad value travels on into your calendar code and breaks things later, far from where the mistake happened.
- **Why `date` and `time` types, not strings?** Pydantic parses and rejects impossible dates for you. It also matches how the project already avoids letting small models do date work (see `_resolve_when` in `agent_tools.py`).
- **Why the quote?** It makes every item checkable by a human and by code. If the quote isn't in the email, the item is suspect.
- **Why one retry?** The first error message often lets the model fix the problem. If it fails twice with the error in front of it, a third try rarely helps and just costs time on a local model.
- **Why `temperature: 0`?** Extraction should be repeatable, not creative.
- **Why the "untrusted data" markers?** The email body is text from outside. This tells the model not to obey instructions inside it (prompt injection).

## 6. What you need to do

1. **Get a model that exists.** `Agent/Agent.py` sets `MODEL = "qwen2.5:14b"`. Run `ollama pull qwen2.5:14b`, or change `MODEL` to one you have (e.g. `qwen2.5:3b`).
2. **Select the right Python interpreter in VS Code** (Python 3.12) so pydantic is found.
3. **Run it** from the repo root: `python -m Extract.extract_email`. Look at the printed JSON and the files in `output/`.
4. **Read the results critically.** For each sample, ask: is every item real? Are dates right? Is anything missing? This is the part no validation can do.
5. **Experiment** (your learning project):
   - Add a check that `due_date` is not before the email's sent date.
   - Add a check that a date in the output also appears in the email text.
   - Compare `qwen2.5:3b` with `14b` on the same samples and see how often the retry runs.
   - Make a change to the schema (e.g. add `location: str | None`) and watch Layer 1 and Layer 2 adapt.
   - Break things on purpose: change the prompt so the model must return `priority: "urgent"` and see what the retry does.

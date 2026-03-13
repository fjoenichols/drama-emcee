# CLAUDE.md — Drama Emcee

> **Sync note:** This file is a mirror of `AGENTS.md`. Both files must be kept identical in content (except for this header block and the corresponding note in `AGENTS.md`). When updating one, update the other.

Guidelines for AI agents and contributors working in this repository.

---

## Project Overview

**drama-emcee** is a Discord bot for the World of Warcraft guild **Drama Club** on US Mug'thol. It integrates with the Blizzard Battle.net API to fetch guild roster and crafting profession data, caches that data in Redis, and exposes it to guild members via Discord slash commands.

The bot is written in Python using `discord.py` and is intended to be a long-lived, single-repo home for all of Drama Club's Discord tooling — modular and easy to grow over time.

---

## Architecture

The project is divided into four layers, each with a clear responsibility:

### `cogs/` — Discord Command Modules
Each file is a `discord.py` Cog: a self-contained class that groups related slash commands. Cogs are loaded at startup by `bot.py` via the `COGS` list. Cogs **only** handle the Discord interaction surface — they receive user input, call into `services/`, and send a response. They contain no business logic or Redis/API calls of their own.

### `services/` — Business Logic & Integrations
Pure Python modules with no Discord dependency. Three modules:
- **`blizzard.py`** — all calls to the Battle.net API (wraps `blizzardapi2`)
- **`cache.py`** — all Redis reads and writes; owns the key schema
- **`professions.py`** — domain logic for profession/recipe queries; calls `cache.py`

### `tasks/` — Background / Scheduled Tasks
Standalone scripts that can be run from the CLI (`python -m tasks.<name>`) or called programmatically. Tasks use `services/` and should never import from `cogs/`. `profession_sync.py` is the canonical example. Nightly cron tasks:
- **`mythic_plus_ratings.py`** — fetches M+ ratings for all guild members across all historical seasons and persists them to the database; nightly cron
- **`mythic_plus_leaderboard.py`** — queries the DB for the top 10 ratings in the current active season and posts them to Discord; run after `mythic_plus_ratings`
- **`refresh_static_data.py`** — populates `wow_classes` and `wow_races` lookup tables from the Blizzard game data API; run once at setup and after major game patches

### `configs/` — Secrets & Connection Config
Contains live config files (`blizz_conf.py`, `discord_conf.py`, `redis_conf.py`) that are **gitignored**. Example files (`*_example.py`) are committed and serve as the template for new contributors.

### Dependency Flow
```
main.py
  └── bot.py
        └── cogs/           (Discord layer)
              └── services/  (business logic)
                    ├── blizzard.py  (Battle.net API)
                    └── cache.py     (Redis)

tasks/                       (uses services/ directly)
tests/                       (tests services/ in isolation)
```

---

## Coding Standards

- **Python 3.10+** — use union types (`X | None`) and f-strings throughout.
- **Type hints** — all function signatures must include parameter and return type annotations.
- **Docstrings** — every public function and class needs a one-line docstring. Multi-line is welcome for complex logic.
- **Module-level docstring** — every file should open with a `"""..."""` block describing its purpose.
- **Naming** — `snake_case` for files, functions, and variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for module-level constants.
- **Private helpers** — prefix with `_` (e.g., `_build_crafter_lines`) for functions not intended to be called from outside the module.
- **One Cog per feature domain** — don't put unrelated commands in the same Cog. Create a new file in `cogs/` instead.
- **No top-level side effects** — modules must not execute code on import (no API calls, no Redis connections at module level). `profession_sync.py` uses an `if __name__ == "__main__"` guard as the pattern to follow.
- **Error handling** — catch narrow exceptions where possible; avoid bare `except:` clauses. Log or print a meaningful message when catching.
- **Formatting** — `black` is in `requirements.txt`; format before committing.

---

## Workflow

### Adding a new command group
1. Create `cogs/<feature>.py` following the pattern in `cogs/general.py`.
2. Add `"cogs.<feature>"` to the `COGS` list in `bot.py`.
3. If the feature needs data logic, add a corresponding module to `services/`.
4. Add tests to `tests/test_<feature>.py`.

### Adding a new scheduled task
1. Create `tasks/<task_name>.py` with a `run_<task_name>()` function as the entry point.
2. Guard CLI execution with `if __name__ == "__main__": run_<task_name>()`.
3. Schedule via cron or a similar tool — see `README.MD` for the cron example.

### Adding a new config value
1. Add the value to `configs/<service>_conf_example.py` with a placeholder.
2. Document it in `README.MD` under the Setup section.

### Running tests
```bash
pytest tests/
```

### Running the profession sync manually
```bash
python -m tasks.profession_sync
```

---

## Things to Avoid

- **Don't import `discord` in `services/` or `tasks/`** — those layers must stay framework-agnostic and testable without a Discord client.
- **Don't add Redis key strings as string literals scattered across the codebase** — all key construction belongs in `services/cache.py` so the key schema stays in one place.
- **Don't add guild-specific constants (guild slug, realm, region) outside of `tasks/`** — the bot commands should work generically via arguments; only the sync task needs the hardcoded guild identity.
- **Don't put command logic inside `bot.py`** — `bot.py` is a loader, not a feature file. All commands live in `cogs/`.
- **Don't run top-level code in modules** — scripts that need to run something on invocation use `if __name__ == "__main__"`.
- **Don't commit real config files** — `blizz_conf.py`, `discord_conf.py`, and `redis_conf.py` are gitignored; only the `*_example.py` versions are tracked.
- **Don't swallow exceptions silently** — bare `except: pass` blocks hide bugs. At minimum print a message or log the error.

---

## Definition of Done
Before considering any task complete, you must:

1. Append an entry to `AGENT_CHANGELOG.md`:
   - One entry per calendar date — if today's date already exists, add sub-bullets to it rather than creating a new top-level entry
   - Top-level format: `- [YYYY-MM-DD] [short summary of the session/task]`
   - Use indented sub-bullets (`  - ...`) for individual file/detail items — avoid walls of text
   - Be specific — include filenames and what was modified
2. Update `README.md` if any of the following changed:
   - Installation or setup steps
   - How to run the project
   - New or removed features
   - Environment variables or configuration
3. Update `AGENTS.md` **and** `CLAUDE.md` if any of the following changed:
   - Project architecture or key directories
   - Coding standards or conventions
   - Available tools or MCP servers
   - Workflow rules

Do not report a task as complete until all applicable steps above are done.

---

## MCP / Tools

- Serena is available for semantic code navigation — prefer it over reading entire files.

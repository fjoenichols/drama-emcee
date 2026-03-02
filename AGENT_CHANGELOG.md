# Agent Changelog

A running log of changes made by AI agents in this repository.

---

- [2026-03-01] Initial project restructuring and documentation pass.
  - Restructured the project from a flat script layout into a modular package architecture
  - Created `cogs/` with `general.py` (/ping, /roll) and `professions.py` (/who_knows_recipe) as discord.py Cogs
  - Created `services/` with `blizzard.py` (Battle.net API wrapper), `cache.py` (all Redis operations), and `professions.py` (recipe query business logic)
  - Created `tasks/` with `profession_sync.py` refactored from a top-level script into importable functions with a `run_sync()` entry point and `if __name__ == "__main__"` guard
  - Created `tests/` with `test_professions.py` scaffolding unit tests for the professions service
  - Rewrote `bot.py` to use the Cog loader pattern with a `COGS` list
  - Added module-level docstring to `main.py`
  - Deleted old flat files `caching.py`, `utility.py`, and root-level `profession_sync.py`
  - Updated `README.MD` with full setup instructions, directory map, and workflow guidance
  - Created `AGENTS.md` with Project Overview, Architecture, Coding Standards, Workflow, Things to Avoid, Definition of Done, and MCP/Tools sections
  - Audited all files for AGENTS.md compliance: added missing docstrings across `bot.py`, `cogs/general.py`, `cogs/professions.py`, and `services/cache.py`; removed unused imports in `cogs/general.py`, `tasks/profession_sync.py`, and `tests/test_professions.py`; replaced silent `except: pass` with a printed error in `tasks/profession_sync.py`; added type annotations to test methods; added module-level docstrings to all three `configs/*_example.py` files
  - Updated `AGENTS.md` Definition of Done to require indented sub-bullets in changelog entries instead of semicolon-separated text
  - Updated `AGENTS.md` Definition of Done to enforce one entry per calendar date (sub-bullets only if same date)
  - Added cross-platform test infrastructure: `Dockerfile`, `Makefile`, and `.github/workflows/test.yml`
    - `Dockerfile` — `python:3.12-slim` base; copies repo, installs deps via `pip3`, default `CMD` runs `python3 -m pytest tests/ -v`
    - `Makefile` — three targets: `make test` (Docker), `make test-local` (direct `python3 -m pytest`), `make install` (local pip3 setup)
    - `.github/workflows/test.yml` — triggers on push/PR to `main`; uses `actions/setup-python@v5` with Python 3.12; runs `python3 -m pytest tests/ -v`
    - `README.MD` — expanded "Running Tests" section documenting all three options (Docker, local Makefile, GitHub Actions)
  - Updated `Makefile` and `README.MD` to use a local virtualenv (`.venv/`) for the `test-local` and `install` targets; `make test-local` auto-creates and populates `.venv/` via `python3 -m venv` before running pytest — no manual `source` step required
  - Added `configs/__init__.py` to make `configs/` a proper Python package; without it the venv's `sys.path` could not resolve `from configs import redis_conf` (namespace package limitation); updated `README.MD` setup step 1 to use `python3 -m venv .venv` + `.venv/bin/pip3 install`

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

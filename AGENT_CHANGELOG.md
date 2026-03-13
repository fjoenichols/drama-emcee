# Agent Changelog

A running log of changes made by AI agents in this repository.

---

- [2026-03-12] Leaderboard uses dedicated Discord webhook
  - Added `LEADERBOARD_WEBHOOK_URL` to `configs/discord_conf_example.py`
  - Updated `tasks/mythic_plus_leaderboard.py` to post to `discord_conf.LEADERBOARD_WEBHOOK_URL` instead of the shared alert webhook

- [2026-03-12] Add wow_classes and wow_races static lookup tables
  - Added `wow_classes` and `wow_races` tables to `services/database.py` with `upsert_class`, `upsert_race`, `get_all_classes`, `get_all_races` functions
  - Added `get_playable_classes_index()` and `get_playable_races_index()` wrappers to `services/blizzard.py`
  - Created `tasks/refresh_static_data.py`: populates both lookup tables from the Blizzard game data API in two API calls; prints a formatted summary; intended to be run once at setup and after major patches

- [2026-03-12] Full historical M+ season tracking with smart nightly sync
  - Added `mythic_keystone_seasons` table to `services/database.py` to persist season metadata (api_id, name, is_current); added 5 new functions: `upsert_season`, `get_current_season`, `get_all_seasons`, `get_ended_seasons_missing_for_character`, `get_mythic_plus_for_character_season`; updated `get_latest_mythic_plus_season` to prefer seasons table with fallback for backward compatibility
  - Updated `services/blizzard.py`: added `get_mythic_keystone_season_detail()` wrapper to fetch season name from game data API on first encounter
  - Rewrote `tasks/mythic_plus_ratings.py`: removed `SEASON_COUNT=4` limit; now tracks all historical seasons; current season always refreshed nightly; ended seasons only fetched for characters with no existing record (backfill); season names persisted from API; supports `--current-only` flag for narrow terminal output
  - Updated `tasks/mythic_plus_leaderboard.py`: now uses `get_current_season()` for season name and ID instead of raw API ID string; leaderboard now shows e.g. "The War Within Season 2" instead of "14"
  - Added `TestMythicPlusSeasons` class to `tests/test_database.py` with 8 new tests covering all new DB functions; all 12 tests pass

- [2026-03-12] Add M+ rating DB persistence, leaderboard task, and CLAUDE.md
  - Created `tasks/mythic_plus_ratings.py`: standalone script that fetches and prints M+ ratings for all guild members across the 4 most recent seasons (3 previous + current); upserts character and M+ records to the database; intended for nightly cron
  - Created `tasks/mythic_plus_leaderboard.py`: standalone script that queries the DB for the top 10 ratings in the most recent active season and posts them to the Discord webhook; intended for nightly cron after ratings sync
  - Updated `services/blizzard.py`: added `get_mythic_keystone_seasons_index()` and `get_character_mythic_keystone_season()` wrappers
  - Updated `services/database.py`: added `get_top_mythic_plus()` and `get_latest_mythic_plus_season()` query functions
  - Created `CLAUDE.md` as a mirror of `AGENTS.md`; both files updated with sync notes and Definition of Done updated to require keeping both in sync

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

- [2026-03-09] Added SQLite database infrastructure and roster sync task.
  - Created `services/database.py` with comprehensive SQLite database service for guild roster data
  - Implemented database schema with tables for characters, professions, recipes, Mythic+ ratings, and PvP rankings
  - Added CRUD operations for all entity types with proper upsert functionality
  - Created `tasks/roster_sync.py` to populate database with guild roster data from Battle.net API
  - Implemented character and profession processing with recipe data extraction
  - Added Discord webhook notifications for sync completion/failure
  - Created `tests/test_database.py` with comprehensive unit tests for database operations
  - Added `test_roster_sync.py` verification script for component testing
  - Updated `README.MD` to document new files and project structure
  - Database service supports environment variable override for DB path for testing

- [2026-03-09] Fixed roster sync error with member rank data handling.
  - Fixed "'int' object has no attribute 'get'" error in `tasks/roster_sync.py` when processing member data
  - Corrected assumption that member rank is a dictionary; it's actually an integer in the Blizzard API
  - Modified `process_member` function to properly handle rank data as an integer
  - Added robust error handling for different possible rank data types

- [2026-03-09] Improved error handling for characters without professions.
  - Added specific handling for 404 errors when fetching character professions
  - Characters without professions now log an informative message instead of an error
  - This reduces noise in the logs and correctly identifies when a character simply has no professions
  - The sync process continues smoothly without interruption

- [2026-03-09] Improved database connection management to prevent locking issues.
  - Implemented context manager pattern for all database connections in `services/database.py`
  - Added `DatabaseConnection` class to ensure proper connection cleanup
  - Updated all database functions to use the context manager for automatic connection closing
  - This should resolve "database is locked" errors when trying to access the database file after script execution
  - Improved reliability of database operations with better resource management

- [2026-03-09] Fixed character table schema and data extraction
  - Added rank, race_id, and class_id columns to characters table
  - Corrected faction data extraction to use character.faction.type instead of guild rank
  - Updated roster sync task to properly extract and store all character attributes
  - Modified database service to handle new character attributes
  - Updated tests to reflect new character table schema

- [2026-03-09] Removed duplicate class column from characters table
  - Removed redundant class column from characters table
  - Updated database service and roster sync task to remove class parameter
  - Modified tests to reflect removal of class column
  - Class names are no longer stored; only class IDs are stored for efficiency

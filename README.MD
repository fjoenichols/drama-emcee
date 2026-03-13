# drama-emcee

A Discord bot for the World of Warcraft guild **Drama Club** on US Mug'thol.

Integrates with the [Battle.net API](https://develop.battle.net/) to query guild roster and crafting profession data, cached in Redis for fast Discord responses.

---

## Features

| Slash Command | Description |
|---|---|
| `/ping` | Show bot latency |
| `/roll d` | Roll a die with *d* sides |
| `/who_knows_recipe <recipe>` | List guild members who know a specific crafting recipe |

---

## Project Structure

```
drama-emcee/
│
├── main.py                        # Entry point — run this to start the bot
├── bot.py                         # Bot init: loads Cogs, registers events, starts client
├── requirements.txt
│
├── configs/                       # Connection secrets (gitignored — see *_example.py files)
│   ├── blizz_conf_example.py
│   ├── discord_conf_example.py
│   └── redis_conf_example.py
│
├── cogs/                          # Discord command modules (one file per feature group)
│   ├── general.py                 # /ping, /roll
│   └── professions.py             # /who_knows_recipe
│
├── services/                      # Business logic & external API integrations
│   ├── blizzard.py                # Battle.net API calls
│   ├── cache.py                   # Redis read/write operations
│   └── professions.py             # Profession & recipe query logic
│
├── tasks/                         # Background / scheduled tasks
│   ├── profession_sync.py         # Rebuilds the profession/recipe cache from Battle.net
│   └── roster_sync.py             # Populates SQLite database with guild roster data
│
└── tests/                         # Unit tests (pytest)
    ├── test_database.py           # Database service tests
    └── test_professions.py        # Profession service tests
```

---

## Setup

### 1. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt
```

Or use the Makefile shortcut:

```bash
make install
```

### 2. Create config files

Copy each example file in `configs/` and fill in your credentials:

```bash
cp configs/blizz_conf_example.py    configs/blizz_conf.py
cp configs/discord_conf_example.py  configs/discord_conf.py
cp configs/redis_conf_example.py    configs/redis_conf.py
```

Edit each file with your:
- **Battle.net** client ID and secret (from [develop.battle.net](https://develop.battle.net/))
- **Discord** bot token and webhook URL
- **Redis** hostname, port, username, and password

### 3. Run an initial profession sync

Before the recipe commands have any data, run the sync task:

```bash
python -m tasks.profession_sync
```

This fetches the full guild roster and every member's profession data from Battle.net, then builds searchable recipe indexes in Redis. It posts a completion message to your Discord webhook when done.

### 4. Start the bot

```bash
python main.py
```

---

## Adding a New Feature

1. Create a new file in `cogs/`, e.g. `cogs/raiding.py`, following the pattern in `cogs/general.py`.
2. Register it in the `COGS` list in `bot.py`.
3. If the feature needs new API calls or data logic, add modules to `services/`.
4. If it needs a scheduled/batch task, add a module to `tasks/`.

---

## Running the Profession Sync on a Schedule

The sync script is designed to be run via cron or any scheduler:

```bash
# Example: run every day at 3 AM
0 3 * * * cd /path/to/drama-emcee && python -m tasks.profession_sync
```

---

## Running Tests

The test suite uses `pytest` with mocked dependencies — no live Redis or Battle.net connection is required.

### Option 1 — Docker (recommended, cross-platform)

Works identically on Windows, macOS, and Linux. Requires [Docker](https://docs.docker.com/get-docker/) to be installed.

```bash
docker build -t drama-emcee-test .
docker run --rm drama-emcee-test
```

Or via the Makefile shortcut:

```bash
make test
```

### Option 2 — Local Python (Mac / Linux fast path)

Requires Python 3. The Makefile manages a local virtualenv at `.venv/` automatically — no manual `source` step needed.

```bash
make test-local
# creates .venv/ if absent, installs deps into it, then runs: python3 -m pytest tests/ -v
```

To set up the virtualenv and install dependencies without running tests:

```bash
make install
```

### Option 3 — GitHub Actions (automatic, on push / PR)

Tests run automatically in CI on every push and pull request to `main`. No local setup needed — just open a PR and the workflow will report results. See `.github/workflows/test.yml`.

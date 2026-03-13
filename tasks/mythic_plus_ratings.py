"""
Mythic Plus Ratings Task

Fetches Mythic+ ratings for every guild member across all known Mythic Keystone
seasons and writes the results to the database.

Season handling:
- The current (active) season is always refreshed for every character.
- Ended seasons are immutable — they are only fetched for characters that have
  no record yet (first-time backfill for new members or initial deployment).
- Season metadata (name, current flag) is synced from the Blizzard game data
  API at the start of each run. Season names are fetched once on first encounter
  and cached in the database thereafter.

Intended to run nightly via cron.

Usage (CLI):
    python -m tasks.mythic_plus_ratings              # shows all seasons
    python -m tasks.mythic_plus_ratings --current-only  # shows only current season
"""

import sys
import logging
import time

from services import blizzard, database

# Guild information
GUILD_SLUG = "drama-club"
GUILD_REALM_SLUG = "mugthol"
REGION = "us"
LOCALE = "en_US"

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _get_season_rating(realm_slug: str, character_name: str, season_id: int) -> float:
    """Return a character's M+ rating for a given season, or 0.0 if unavailable."""
    try:
        data = blizzard.get_character_mythic_keystone_season(
            REGION, LOCALE, realm_slug, character_name, season_id
        )
        return float(data.get("mythic_rating", {}).get("rating", 0.0))
    except Exception as e:
        if "404" in str(e):
            return 0.0
        logger.warning(
            f"Unexpected error fetching M+ rating for {character_name} "
            f"(season {season_id}): {e}"
        )
        return 0.0


def _sync_seasons_metadata() -> tuple[int, list[int]]:
    """
    Sync season metadata from the Blizzard API to the database.

    Fetches the seasons index, resolves any new seasons (fetching their names
    from the game data API on first encounter), and updates the is_current flag.

    Returns:
        Tuple of (current_api_id, all_api_ids_sorted_asc).
    """
    existing = {s["api_id"]: s for s in database.get_all_seasons()}

    index = blizzard.get_mythic_keystone_seasons_index(REGION, LOCALE)
    all_api_ids = sorted(s["id"] for s in index.get("seasons", []) if "id" in s)
    current_api_id: int = index["current_season"]["id"]

    for api_id in all_api_ids:
        if api_id in existing:
            name = existing[api_id]["name"]
        else:
            try:
                detail = blizzard.get_mythic_keystone_season_detail(REGION, LOCALE, api_id)
                name = detail.get("name") or f"Season {api_id}"
            except Exception as e:
                logger.warning(f"Could not fetch name for season {api_id}: {e}")
                name = f"Season {api_id}"

        database.upsert_season(
            api_id=api_id,
            name=name,
            is_current=(api_id == current_api_id),
        )

    return current_api_id, all_api_ids


def run() -> None:
    """Fetch M+ ratings for all guild members, persist to DB, and print results."""
    start = time.time()
    current_only = "--current-only" in sys.argv

    # --- Phase 1: Sync season metadata ---
    print("Syncing season metadata...")
    current_api_id, all_api_ids = _sync_seasons_metadata()
    all_seasons = {s["api_id"]: s for s in database.get_all_seasons()}
    current_name = all_seasons[current_api_id]["name"]
    print(f"Current season: {current_name} (ID {current_api_id})")
    print(f"All known seasons: {all_api_ids}\n")

    # --- Phase 2: Fetch guild roster ---
    print(f"Fetching guild roster for {GUILD_SLUG}...")
    roster_data = blizzard.get_guild_roster(REGION, LOCALE, GUILD_REALM_SLUG, GUILD_SLUG)
    members = roster_data.get("members", [])
    print(f"Retrieved {len(members)} guild members. Fetching M+ ratings...\n")

    # --- Phase 3: Build table header ---
    display_ids = [current_api_id] if current_only else all_api_ids
    display_labels = [all_seasons[sid]["name"].replace("The War Within ", "TWW ") for sid in display_ids]

    col_name = 22
    col_realm = 16
    col_rating = 10

    header = f"{'Character':<{col_name}} {'Realm':<{col_realm}}" + "".join(
        f" {label:>{col_rating}}" for label in display_labels
    )
    separator = "-" * len(header)
    print(header)
    print(separator)

    # --- Phase 4: Per-character sync ---
    processed = 0
    db_written = 0

    for member in members:
        character_data = member.get("character", {})
        name: str = character_data.get("name", "")
        realm: str = character_data.get("realm", {}).get("slug", "")

        if not name or not realm:
            continue

        try:
            char_id = database.upsert_character(
                name=name.lower(),
                realm=realm.lower(),
                region=REGION,
            )
        except Exception as e:
            logger.warning(f"Could not upsert character {name}-{realm}: {e}")
            continue

        fetched: dict[int, float] = {}

        # Current season: always refresh
        rating = _get_season_rating(realm, name.lower(), current_api_id)
        database.upsert_mythic_plus(char_id, str(current_api_id), rating)
        fetched[current_api_id] = rating
        db_written += 1

        # Ended seasons: backfill only where no record exists
        for season_str in database.get_ended_seasons_missing_for_character(char_id):
            sid = int(season_str)
            backfill_rating = _get_season_rating(realm, name.lower(), sid)
            database.upsert_mythic_plus(char_id, season_str, backfill_rating)
            fetched[sid] = backfill_rating
            db_written += 1

        # Fill display ratings not already fetched (from DB)
        display_ratings: list[float] = []
        for sid in display_ids:
            if sid in fetched:
                display_ratings.append(fetched[sid])
            else:
                row = database.get_mythic_plus_for_character_season(char_id, str(sid))
                display_ratings.append(row["score"] if row else 0.0)

        row_str = f"{name:<{col_name}} {realm:<{col_realm}}" + "".join(
            f" {r:>{col_rating}.1f}" for r in display_ratings
        )
        print(row_str)
        processed += 1

    elapsed = time.time() - start
    print(separator)
    print(
        f"\nDone. {processed} characters processed, "
        f"{db_written} DB records written in {elapsed:.1f}s."
    )


if __name__ == "__main__":
    run()

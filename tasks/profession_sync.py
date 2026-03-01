"""
Profession Sync Task

Clears and rebuilds the Redis profession/recipe cache from the Battle.net API.
Can be run directly from the command line or called programmatically.

Usage (CLI):
    python -m tasks.profession_sync

Usage (programmatic):
    from tasks.profession_sync import run_sync
    run_sync()
"""

import time
from configs import discord_conf
from discord_webhook import DiscordWebhook
from services import blizzard, cache

GUILD_SLUG = "drama-club"
GUILD_REALM_SLUG = "mugthol"
REGION = "us"
LOCALE = "en_US"

WEBHOOK_URL = discord_conf.WEBHOOK_URL


def run_sync() -> None:
    """Full profession sync: clears cache, fetches fresh data, rebuilds indexes."""
    start_time = time.time()

    _clear_cache()
    guild_roster = _refresh_guild_roster()
    _refresh_character_professions(guild_roster)
    _rebuild_profession_indexes(guild_roster)

    elapsed_minutes = (time.time() - start_time) / 60
    success_message = f"Profession Sync Successful. Execution time: {elapsed_minutes:.2f} minutes."
    print(success_message)

    webhook = DiscordWebhook(url=WEBHOOK_URL, content=success_message)
    webhook.execute()


def _clear_cache() -> None:
    """Wipe all profession-related Redis keys before a fresh sync."""
    print("Clearing guild_roster cache")
    cache.delete_keys("guild_roster")

    print("Clearing player_professions cache")
    cache.delete_keys("player_professions:*")

    print("Clearing professions cache")
    cache.delete_keys("professions:*")


def _refresh_guild_roster() -> list:
    """Fetch the guild roster from Battle.net and cache it; return the members list."""
    print(f"Getting roster for {GUILD_SLUG} on {GUILD_REALM_SLUG}")
    roster_data = blizzard.get_guild_roster(REGION, LOCALE, GUILD_REALM_SLUG, GUILD_SLUG)
    cache.set_guild_roster(roster_data)
    return roster_data.get("members", [])


def _refresh_character_professions(guild_roster: list) -> None:
    """Fetch and cache profession data for every member of the guild roster."""
    print(f"Getting character profession updates for {GUILD_SLUG} on {GUILD_REALM_SLUG}")
    for member in guild_roster:
        try:
            character_name = member.get("character", {}).get("name", "").lower()
            realm_slug = member.get("character", {}).get("realm", {}).get("slug", "")
            print(f"  updating {character_name}+{realm_slug}")
            data = blizzard.get_character_professions(REGION, LOCALE, realm_slug, character_name)
            cache.set_character_professions(character_name, realm_slug, data)
        except Exception:
            print(f"  error updating {character_name}+{realm_slug}")


def _rebuild_profession_indexes(guild_roster: list) -> None:
    """
    Walk each character's cached profession data and build the searchable
    profession / tier / recipe indexes in Redis.
    """
    for member in guild_roster:
        try:
            character_name = member.get("character", {}).get("name", "").lower()
            realm_slug = member.get("character", {}).get("realm", {}).get("slug", "")
            player_slug = f"{character_name}+{realm_slug}"

            player = cache.get_character_professions(character_name, realm_slug)
            if not player:
                continue

            print(player_slug)

            for primary_profession in player.get("primaries", []):
                profession = primary_profession.get("profession", {}).get("name", "").lower()
                profession_key = f"professions: {profession}"

                # Add to profession list
                cache.append_to_profession_list(profession_key, player_slug)

                for tier in primary_profession.get("tiers", []):
                    tier_name = tier.get("tier", {}).get("name", "").lower()
                    tier_key = f"{profession_key} tier: {tier_name}"

                    # Add to tier list
                    cache.append_to_profession_list(tier_key, player_slug)

                    for recipe in tier.get("known_recipes", []):
                        recipe_name = recipe.get("name", "").lower()
                        recipe_key = f"professions: recipes: {recipe_name}"

                        # Add to recipe list
                        cache.append_to_profession_list(recipe_key, player_slug)

        except Exception as e:
            print(f"  error rebuilding indexes for {player_slug}: {e}")


if __name__ == "__main__":
    run_sync()

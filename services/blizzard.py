"""
Blizzard Battle.net API service layer.
Wraps blizzardapi2 calls so the rest of the app never imports blizzardapi2 directly.
"""

from datetime import datetime
import re

from configs import blizz_conf

api_client = blizz_conf.api_client

# Monkey-patch blizzardapi2's datetime parser to handle timestamps without microseconds
try:
    import blizzardapi2.utils as _bapi_utils
    _orig_parse = _bapi_utils.parse_datetime

    def _safe_parse_datetime(value):
        if not isinstance(value, str):
            return _orig_parse(value)
        # Normalize: add .000000 if microseconds missing (e.g. '2026-04-11T15:00:01Z')
        import re
        if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
            value = value.replace('Z', '.000000Z')
        return _orig_parse(value)

    _bapi_utils.parse_datetime = _safe_parse_datetime
except Exception:
    pass  # blizzardapi2 version may have changed; fail silently


def _normalize_datetime(value):
    """Normalize datetime strings from the Blizzard API.

    The API sometimes returns timestamps like '2026-04-11T15:00:01Z'
    (no microseconds) which blizzardapi2 tries to parse as
    '%Y-%m-%dT%H:%M:%S.%fZ'. This helper ensures microseconds are present
    so the parsing always succeeds.
    """
    if not isinstance(value, str):
        return value
    # Already has microseconds — return as-is
    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z', value):
        return value
    # Add .000000 for microseconds if missing
    return re.sub(r'(T\d{2}:\d{2}:\d{2})Z', r'\1.000000Z', value)


def get_guild_roster(region: str, locale: str, guild_realm_slug: str, guild_slug: str) -> dict:
    """Fetch the full guild roster from the Battle.net API."""
    return api_client.wow.profile.get_guild_roster(region, locale, guild_realm_slug, guild_slug)


def get_character_professions(region: str, locale: str, realm_slug: str, character_name: str) -> dict:
    """Fetch a character's profession summary from the Battle.net API."""
    return api_client.wow.profile.get_character_professions_summary(
        region, locale, realm_slug, character_name
    )


def get_playable_classes_index(region: str, locale: str) -> dict:
    """Fetch the index of all playable WoW classes from the game data API."""
    return api_client.wow.game_data.get_playable_classes_index(region, locale)


def get_playable_races_index(region: str, locale: str) -> dict:
    """Fetch the index of all playable WoW races from the game data API."""
    return api_client.wow.game_data.get_playable_races_index(region, locale)


def get_mythic_keystone_season_detail(region: str, locale: str, season_id: int) -> dict:
    """Fetch metadata for a single Mythic Keystone season (name, etc.) from the game data API."""
    return api_client.wow.game_data.get_mythic_keystone_season(region, locale, season_id)


def get_mythic_keystone_seasons_index(region: str, locale: str) -> dict:
    """Fetch the index of all Mythic Keystone seasons from the game data API."""
    return api_client.wow.game_data.get_mythic_keystone_seasons_index(region, locale)


def get_character_mythic_keystone_season(
    region: str, locale: str, realm_slug: str, character_name: str, season_id: int
) -> dict:
    """Fetch a character's Mythic Keystone rating for a specific season."""
    return api_client.wow.profile.get_character_mythic_keystone_profile_season_details(
        region, locale, realm_slug, character_name, season_id
    )

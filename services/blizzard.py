"""
Blizzard Battle.net API service layer.
Wraps blizzardapi2 calls so the rest of the app never imports blizzardapi2 directly.
"""

from configs import blizz_conf

api_client = blizz_conf.api_client


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

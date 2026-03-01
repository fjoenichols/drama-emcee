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

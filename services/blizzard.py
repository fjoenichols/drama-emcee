"""
Blizzard Battle.net API service layer.
Wraps blizzardapi2 calls so the rest of the app never imports blizzardapi2 directly.
"""

from configs import blizz_conf

# Patch blizzardapi2's Api class before api_client is created.
# _is_token_expired() uses strptime('%Y-%m-%dT%H:%M:%S.%fZ') which crashes
# when the OAuth server returns a timestamp without fractional seconds
# (e.g. '2026-04-11T21:45:21Z').
from blizzardapi2.api import Api
_original = Api._is_token_expired

def _safe(self):
    try:
        return _original(self)
    except ValueError:
        return True

Api._is_token_expired = _safe

api_client = blizz_conf.api_client


def get_guild_roster(region: str, locale: str, guild_realm_slug: str, guild_slug: str) -> dict:
    return api_client.wow.profile.get_guild_roster(region, locale, guild_realm_slug, guild_slug)


def get_character_professions(region: str, locale: str, realm_slug: str, character_name: str) -> dict:
    return api_client.wow.profile.get_character_professions_summary(region, locale, realm_slug, character_name)


def get_playable_classes_index(region: str, locale: str) -> dict:
    return api_client.wow.game_data.get_playable_classes_index(region, locale)


def get_playable_races_index(region: str, locale: str) -> dict:
    return api_client.wow.game_data.get_playable_races_index(region, locale)


def get_mythic_keystone_season_detail(region: str, locale: str, season_id: int) -> dict:
    return api_client.wow.game_data.get_mythic_keystone_season(region, locale, season_id)


def get_mythic_keystone_seasons_index(region: str, locale: str) -> dict:
    return api_client.wow.game_data.get_mythic_keystone_seasons_index(region, locale)


def get_character_mythic_keystone_season(region: str, locale: str, realm_slug: str, character_name: str, season_id: int) -> dict:
    return api_client.wow.profile.get_character_mythic_keystone_profile_season_details(
        region, locale, realm_slug, character_name, season_id
    )

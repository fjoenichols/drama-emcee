"""
Blizzard Battle.net API service layer.
Wraps blizzardapi2 calls so the rest of the app never imports blizzardapi2 directly.
"""

from configs import blizz_conf

api_client = blizz_conf.api_client

# blizzardapi2's _is_token_expired() parses OAuth server timestamps with strptime
# using a format that requires microseconds (%f). The OAuth server can return
# timestamps without microseconds (e.g. '2026-04-11T15:00:01Z'), causing a
# ValueError crash. Patch it to fall back safely — if we can't parse the
# expiry, treat the token as expired so the next call triggers re-auth.
try:
    from blizzardapi2.api import BattleNetApi

    _orig_is_token_expired = BattleNetApi._is_token_expired

    def _patched_is_token_expired(self):
        try:
            return _orig_is_token_expired(self)
        except ValueError:
            # Unparseable expiry timestamp — treat as expired to force re-auth
            return True

    BattleNetApi._is_token_expired = _patched_is_token_expired
except Exception:
    pass  # blizzardapi2 version may have changed; fail silently


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

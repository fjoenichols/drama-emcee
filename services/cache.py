"""
Redis caching service layer.
All interactions with Redis are centralised here.
"""

from configs import redis_conf
import json

r = redis_conf.r

# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def delete_keys(pattern: str) -> None:
    """Delete all Redis keys that match a glob-style pattern."""
    for key in r.keys(pattern):
        print(f"deleting {key}")
        r.delete(key)


# ---------------------------------------------------------------------------
# Guild roster
# ---------------------------------------------------------------------------

def set_guild_roster(roster: dict) -> None:
    """Cache the full guild roster JSON in Redis."""
    r.set("guild_roster", json.dumps(roster))


def get_guild_roster() -> dict | None:
    """Return the cached guild roster, or None if not present."""
    raw = r.get("guild_roster")
    return json.loads(raw) if raw else None


# ---------------------------------------------------------------------------
# Character professions
# ---------------------------------------------------------------------------

def _profession_key(character_name: str, realm_slug: str) -> str:
    """Build the Redis key for a character's cached profession data."""
    return f"player_professions: {character_name}+{realm_slug}"


def set_character_professions(character_name: str, realm_slug: str, data: dict) -> None:
    """Cache profession data for a single character."""
    r.set(_profession_key(character_name, realm_slug), json.dumps(data))


def get_character_professions(character_name: str, realm_slug: str) -> dict | None:
    """Return cached profession data for a character, or None if not present."""
    raw = r.get(_profession_key(character_name, realm_slug))
    return json.loads(raw) if raw else None


# ---------------------------------------------------------------------------
# Profession / recipe indexes
# ---------------------------------------------------------------------------

def append_to_profession_list(key: str, player_slug: str) -> None:
    """Append a player slug to a profession list key, creating it if absent."""
    existing = r.get(key)
    if existing:
        if player_slug not in existing:
            r.append(key, player_slug + " ")
    else:
        r.set(key, player_slug + " ")


def get_recipe_crafters(recipe: str) -> str | None:
    """Return the raw space-separated crafter list for a recipe, or None."""
    return r.get(f"professions: recipes: {recipe}")

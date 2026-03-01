"""
Profession business-logic service layer.
Contains all query logic related to WoW professions and recipes.
"""

from services import cache


def who_knows_recipe(recipe: str) -> str:
    """
    Returns a formatted Discord message listing all guild members
    who know the given recipe. Returns a 'nobody knows' message if
    the recipe is not found in the cache.
    """
    crafters_raw = cache.get_recipe_crafters(recipe)
    if not crafters_raw:
        return f"Nobody in the guild knows **{recipe.title()}**."

    crafter_lines = _build_crafter_lines(crafters_raw)
    return f"The following players know **{recipe.title()}**\n\n" + crafter_lines


def _build_crafter_lines(crafters_raw: str) -> str:
    """
    Takes the raw space-separated 'name+realm' crafter string from Redis
    and returns a formatted list of 'CharacterName-RealmName' lines.
    """
    slugs = [s for s in crafters_raw.split(" ") if s]
    lines = []

    for slug in slugs:
        character_name, realm_slug = slug.split("+")
        data = cache.get_character_professions(character_name, realm_slug)
        if data:
            proper_name = data.get("character", {}).get("name", character_name)
            proper_realm = data.get("character", {}).get("realm", {}).get("name", realm_slug)
            lines.append(f"> {proper_name}-{proper_realm}")

    return "\n ".join(lines)

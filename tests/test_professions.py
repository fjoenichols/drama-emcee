"""
Tests for services/professions.py

Run with:  pytest tests/
"""

from unittest.mock import patch, MagicMock

from services import professions as profession_service


# ---------------------------------------------------------------------------
# who_knows_recipe
# ---------------------------------------------------------------------------

class TestWhoKnowsRecipe:
    """Unit tests for the who_knows_recipe service function."""

    @patch("services.professions.cache")
    def test_returns_nobody_message_when_recipe_not_cached(self, mock_cache: MagicMock) -> None:
        """Returns a 'nobody knows' message when the recipe key is absent from Redis."""
        mock_cache.get_recipe_crafters.return_value = None

        result = profession_service.who_knows_recipe("runed copper rod")

        assert "Nobody in the guild knows" in result
        assert "Runed Copper Rod" in result

    @patch("services.professions.cache")
    def test_returns_crafter_list_when_recipe_cached(self, mock_cache: MagicMock) -> None:
        """Returns a formatted crafter list when at least one player knows the recipe."""
        mock_cache.get_recipe_crafters.return_value = "dramaplayer+mugthol "
        mock_cache.get_character_professions.return_value = {
            "character": {
                "name": "Dramaplayer",
                "realm": {"name": "Mug'thol"},
            }
        }

        result = profession_service.who_knows_recipe("runed copper rod")

        assert "Runed Copper Rod" in result
        assert "Dramaplayer" in result
        assert "Mug'thol" in result

    @patch("services.professions.cache")
    def test_recipe_name_is_title_cased_in_output(self, mock_cache: MagicMock) -> None:
        """Recipe names are title-cased in the response message regardless of input case."""
        mock_cache.get_recipe_crafters.return_value = None

        result = profession_service.who_knows_recipe("flask of power")

        assert "Flask Of Power" in result

"""
Unit tests for the database service.
"""

import unittest
import tempfile
import os
from services.database import (
    init_db, upsert_character, get_character, get_all_characters,
    upsert_profession, get_character_professions, get_crafters_by_profession,
    add_recipes, get_profession_recipes,
    upsert_season, get_current_season, get_all_seasons,
    get_ended_seasons_missing_for_character, get_mythic_plus_for_character_season,
    upsert_mythic_plus,
)

class TestDatabase(unittest.TestCase):
    """Test cases for the database service."""

    def setUp(self):
        """Set up test database."""
        # Create a temporary database for testing
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        os.environ['DB_PATH'] = self.test_db.name
        init_db()

    def tearDown(self):
        """Clean up test database."""
        os.unlink(self.test_db.name)

    def test_character_operations(self):
        """Test character CRUD operations."""
        # Test upsert character
        char_id = upsert_character("testchar", "testrealm", "us", level=60, faction="HORDE", rank=1, race_id=27, class_id=8)
        self.assertIsInstance(char_id, int)
        self.assertGreater(char_id, 0)
        
        # Test get character
        char = get_character("testchar", "testrealm", "us")
        self.assertIsNotNone(char)
        self.assertEqual(char['name'], "testchar")
        self.assertEqual(char['realm'], "testrealm")
        self.assertEqual(char['level'], 60)
        self.assertEqual(char['faction'], "HORDE")
        self.assertEqual(char['rank'], 1)
        self.assertEqual(char['race_id'], 27)
        self.assertEqual(char['class_id'], 8)
        
        # Test get all characters
        chars = get_all_characters()
        self.assertEqual(len(chars), 1)
        self.assertEqual(chars[0]['name'], "testchar")

    def test_profession_operations(self):
        """Test profession CRUD operations."""
        # Create a character first
        char_id = upsert_character("testchar", "testrealm")
        
        # Test upsert profession
        prof_id = upsert_profession(char_id, "Blacksmithing", 150, 150)
        self.assertIsInstance(prof_id, int)
        self.assertGreater(prof_id, 0)
        
        # Test get character professions
        profs = get_character_professions(char_id)
        self.assertEqual(len(profs), 1)
        self.assertEqual(profs[0]['name'], "blacksmithing")
        self.assertEqual(profs[0]['skill_level'], 150)
        
        # Test get crafters by profession
        crafters = get_crafters_by_profession("Blacksmithing")
        self.assertEqual(len(crafters), 1)
        self.assertEqual(crafters[0]['name'], "testchar")
        self.assertEqual(crafters[0]['skill_level'], 150)

    def test_recipe_operations(self):
        """Test recipe operations."""
        # Create a character and profession
        char_id = upsert_character("testchar", "testrealm")
        prof_id = upsert_profession(char_id, "Blacksmithing")
        
        # Test add recipes
        recipes = [
            {"name": "Dragon Scale Mail", "category": "Armor"},
            {"name": "Thorium Shield Spike", "category": "Shield"}
        ]
        add_recipes(prof_id, recipes)
        
        # Test get profession recipes
        retrieved_recipes = get_profession_recipes(prof_id)
        self.assertEqual(len(retrieved_recipes), 2)
        recipe_names = [r['name'] for r in retrieved_recipes]
        self.assertIn("dragon scale mail", recipe_names)
        self.assertIn("thorium shield spike", recipe_names)

class TestMythicPlusSeasons(unittest.TestCase):
    """Test cases for mythic_keystone_seasons table and related M+ helpers."""

    def setUp(self) -> None:
        """Set up a fresh temporary database for each test."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        os.environ['DB_PATH'] = self.test_db.name
        init_db()

    def tearDown(self) -> None:
        """Remove the temporary database."""
        os.unlink(self.test_db.name)

    def test_upsert_season_insert(self) -> None:
        """upsert_season creates a new row with the correct values."""
        upsert_season(api_id=13, name="The War Within Season 1", is_current=False)
        seasons = get_all_seasons()
        self.assertEqual(len(seasons), 1)
        self.assertEqual(seasons[0]["api_id"], 13)
        self.assertEqual(seasons[0]["name"], "The War Within Season 1")
        self.assertEqual(seasons[0]["is_current"], 0)

    def test_upsert_season_current_clears_others(self) -> None:
        """Marking a season current clears is_current on all other rows."""
        upsert_season(api_id=13, name="The War Within Season 1", is_current=True)
        upsert_season(api_id=14, name="The War Within Season 2", is_current=False)

        # Now mark season 14 as current
        upsert_season(api_id=14, name="The War Within Season 2", is_current=True)

        seasons = {s["api_id"]: s for s in get_all_seasons()}
        self.assertEqual(seasons[13]["is_current"], 0)
        self.assertEqual(seasons[14]["is_current"], 1)

    def test_get_current_season_returns_none_when_empty(self) -> None:
        """get_current_season returns None before any season is inserted."""
        self.assertIsNone(get_current_season())

    def test_get_current_season_returns_correct_row(self) -> None:
        """get_current_season returns the row marked is_current=1."""
        upsert_season(api_id=13, name="Season 1", is_current=False)
        upsert_season(api_id=14, name="Season 2", is_current=True)
        current = get_current_season()
        self.assertIsNotNone(current)
        self.assertEqual(current["api_id"], 14)
        self.assertEqual(current["name"], "Season 2")

    def test_get_ended_seasons_missing_zero_history(self) -> None:
        """Character with no M+ records gets all ended seasons returned."""
        upsert_season(api_id=12, name="Old Season", is_current=False)
        upsert_season(api_id=13, name="Previous Season", is_current=False)
        upsert_season(api_id=14, name="Current Season", is_current=True)

        char_id = upsert_character("newchar", "testrealm")
        missing = get_ended_seasons_missing_for_character(char_id)
        self.assertEqual(sorted(missing), ["12", "13"])

    def test_get_ended_seasons_missing_partial_history(self) -> None:
        """Character with partial history gets only missing ended seasons."""
        upsert_season(api_id=12, name="Old Season", is_current=False)
        upsert_season(api_id=13, name="Previous Season", is_current=False)
        upsert_season(api_id=14, name="Current Season", is_current=True)

        char_id = upsert_character("partialchar", "testrealm")
        upsert_mythic_plus(char_id, "12", 1800.0)  # already has season 12

        missing = get_ended_seasons_missing_for_character(char_id)
        self.assertEqual(missing, ["13"])  # only season 13 is missing

    def test_get_ended_seasons_missing_full_history(self) -> None:
        """Character with all ended seasons covered gets an empty list."""
        upsert_season(api_id=13, name="Previous Season", is_current=False)
        upsert_season(api_id=14, name="Current Season", is_current=True)

        char_id = upsert_character("fullchar", "testrealm")
        upsert_mythic_plus(char_id, "13", 2200.0)

        missing = get_ended_seasons_missing_for_character(char_id)
        self.assertEqual(missing, [])

    def test_get_mythic_plus_for_character_season_missing(self) -> None:
        """Returns None when no record exists for the character+season pair."""
        char_id = upsert_character("testchar", "testrealm")
        result = get_mythic_plus_for_character_season(char_id, "13")
        self.assertIsNone(result)

    def test_get_mythic_plus_for_character_season_found(self) -> None:
        """Returns the correct row when a record exists."""
        char_id = upsert_character("testchar", "testrealm")
        upsert_mythic_plus(char_id, "13", 2450.5)
        result = get_mythic_plus_for_character_season(char_id, "13")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["score"], 2450.5)


if __name__ == '__main__':
    unittest.main()
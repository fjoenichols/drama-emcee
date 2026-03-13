"""
SQLite database service for drama-emcee.

Provides structured storage for guild roster data including character info,
professions, Mythic+ ratings, and PvP rankings. Works alongside Redis as
a persistent data store for more complex queries and historical tracking.

Database Schema:
- characters: Core character information
- professions: Character professions and skill levels
- recipes: Known recipes for each profession
- mythic_plus: Mythic+ dungeon scores and ratings (all historical seasons)
- mythic_keystone_seasons: Season metadata (name, current flag) keyed by Blizzard API ID
- pvp: PvP rankings and statistics
- wow_classes: Static lookup — WoW playable class IDs and names
- wow_races: Static lookup — WoW playable race IDs, names, and faction
"""

import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    """Get the database file path, evaluating environment variable dynamically."""
    return os.environ.get('DB_PATH', 'guild_roster.db')

# For backward compatibility with existing code that references DB_PATH directly
DB_PATH = get_db_path()

def init_db(db_path: str = None) -> None:
    """Initialize the database with all required tables."""
    # Use provided db_path or get it dynamically
    actual_db_path = db_path or get_db_path()
    
    conn = sqlite3.connect(actual_db_path)
    cursor = conn.cursor()
    
    # Create characters table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            realm TEXT NOT NULL,
            region TEXT NOT NULL DEFAULT 'us',
            level INTEGER,
            faction TEXT,
            rank INTEGER,
            race_id INTEGER,
            class_id INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, realm, region)
        )
    """)
    
    # Create professions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            skill_level INTEGER,
            max_skill_level INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters (id),
            UNIQUE(character_id, name)
        )
    """)
    
    # Create recipes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profession_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profession_id) REFERENCES professions (id)
        )
    """)
    
    # Create mythic_plus table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mythic_plus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            season TEXT NOT NULL,
            score REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters (id),
            UNIQUE(character_id, season)
        )
    """)
    
    # Create mythic_keystone_seasons table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mythic_keystone_seasons (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            api_id     INTEGER NOT NULL UNIQUE,
            name       TEXT    NOT NULL,
            is_current INTEGER NOT NULL DEFAULT 0,
            first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create pvp table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pvp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL,
            bracket TEXT NOT NULL,
            rating INTEGER,
            season TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (character_id) REFERENCES characters (id),
            UNIQUE(character_id, bracket, season)
        )
    """)
    
    # Create wow_classes lookup table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wow_classes (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    # Create wow_races lookup table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wow_races (
            id      INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,
            faction TEXT
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


class DatabaseConnection:
    """Context manager for database connections."""
    
    def __enter__(self):
        self.conn = sqlite3.connect(get_db_path())
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'conn'):
            self.conn.close()


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with row factory set for dict-like access."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn


# Character operations
def upsert_character(name: str, realm: str, region: str = "us", level: int = None, faction: str = None, rank: int = None, race_id: int = None, class_id: int = None) -> int:
    """
    Insert or update a character record.
    
    Args:
        name: Character name
        realm: Realm name
        region: Region (default: "us")
        level: Character level
        faction: Character faction
        rank: Guild rank
        race_id: Playable race ID
        class_id: Playable class ID
        
    Returns:
        Character ID
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO characters (name, realm, region, level, faction, rank, race_id, class_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name, realm, region) DO UPDATE SET
                level = excluded.level,
                faction = excluded.faction,
                rank = excluded.rank,
                race_id = excluded.race_id,
                class_id = excluded.class_id,
                last_updated = CURRENT_TIMESTAMP
        """, (
            name.lower(), 
            realm.lower(), 
            region.lower(),
            level,
            faction,
            rank,
            race_id,
            class_id
        ))
        
        # If it was an insert, we get the rowid directly
        # If it was an update, we need to fetch the id
        if cursor.lastrowid == 0:
            cursor.execute("""
                SELECT id FROM characters 
                WHERE name = ? AND realm = ? AND region = ?
            """, (name.lower(), realm.lower(), region.lower()))
            row = cursor.fetchone()
            char_id = row[0] if row else None
        else:
            char_id = cursor.lastrowid
        
        conn.commit()
        
        logger.debug(f"Upserted character {name}-{realm} with ID {char_id}")
        return char_id


def get_character(name: str, realm: str, region: str = "us") -> Optional[Dict]:
    """Get character by name, realm, and region."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM characters 
            WHERE name = ? AND realm = ? AND region = ?
        """, (name.lower(), realm.lower(), region.lower()))
        
        row = cursor.fetchone()
        
        return dict(row) if row else None


def get_all_characters() -> List[Dict]:
    """Get all characters from the database."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM characters ORDER BY name")
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


def get_stale_characters(days: int = 1) -> List[Dict]:
    """
    Get characters whose data is older than specified days.
    
    Args:
        days: Number of days after which data is considered stale
        
    Returns:
        List of stale characters
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM characters 
            WHERE last_updated < datetime('now', '-{} days')
            ORDER BY last_updated ASC
        """.format(days))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


# Profession operations
def upsert_profession(character_id: int, name: str, skill_level: int = 0, max_skill_level: int = 0) -> int:
    """
    Insert or update a profession record.
    
    Args:
        character_id: Character ID
        name: Profession name
        skill_level: Current skill level
        max_skill_level: Maximum skill level
        
    Returns:
        Profession ID
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO professions (character_id, name, skill_level, max_skill_level)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(character_id, name) DO UPDATE SET
                skill_level = excluded.skill_level,
                max_skill_level = excluded.max_skill_level,
                last_updated = CURRENT_TIMESTAMP
        """, (character_id, name.lower(), skill_level, max_skill_level))
        
        # If it was an insert, we get the rowid directly
        # If it was an update, we need to fetch the id
        if cursor.lastrowid == 0:
            cursor.execute("""
                SELECT id FROM professions 
                WHERE character_id = ? AND name = ?
            """, (character_id, name.lower()))
            row = cursor.fetchone()
            prof_id = row[0] if row else None
        else:
            prof_id = cursor.lastrowid
        
        conn.commit()
        
        logger.debug(f"Upserted profession {name} for character ID {character_id}")
        return prof_id


def get_character_professions(character_id: int) -> List[Dict]:
    """Get all professions for a character."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM professions 
            WHERE character_id = ? 
            ORDER BY name
        """, (character_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


def get_crafters_by_profession(profession_name: str) -> List[Dict]:
    """
    Get all characters with a specific profession.
    
    Args:
        profession_name: Name of profession to search for
        
    Returns:
        List of characters with that profession
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, p.skill_level, p.max_skill_level
            FROM characters c
            JOIN professions p ON c.id = p.character_id
            WHERE p.name = ?
            ORDER BY p.skill_level DESC, c.name
        """, (profession_name.lower(),))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


# Recipe operations
def add_recipes(profession_id: int, recipes: List[Dict]) -> None:
    """
    Add recipes to a profession.
    
    Args:
        profession_id: Profession ID
        recipes: List of recipe dictionaries with 'name' and optional 'category'
    """
    if not recipes:
        return
        
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        # Clear existing recipes for this profession
        cursor.execute("DELETE FROM recipes WHERE profession_id = ?", (profession_id,))
        
        # Insert new recipes
        recipe_data = [
            (profession_id, recipe['name'].lower(), recipe.get('category', ''))
            for recipe in recipes
        ]
        
        cursor.executemany("""
            INSERT INTO recipes (profession_id, name, category)
            VALUES (?, ?, ?)
        """, recipe_data)
        
        conn.commit()
        
        logger.debug(f"Added {len(recipes)} recipes to profession ID {profession_id}")


def get_profession_recipes(profession_id: int) -> List[Dict]:
    """Get all recipes for a profession."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM recipes 
            WHERE profession_id = ? 
            ORDER BY name
        """, (profession_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


# Mythic+ operations
def upsert_mythic_plus(character_id: int, season: str, score: float) -> None:
    """
    Insert or update Mythic+ rating for a character.
    
    Args:
        character_id: Character ID
        season: Season identifier
        score: Mythic+ score
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO mythic_plus (character_id, season, score)
            VALUES (?, ?, ?)
            ON CONFLICT(character_id, season) DO UPDATE SET
                score = excluded.score,
                last_updated = CURRENT_TIMESTAMP
        """, (character_id, season, score))
        
        conn.commit()
        
        logger.debug(f"Upserted M+ score {score} for character ID {character_id}")


def get_character_mythic_plus(character_id: int) -> List[Dict]:
    """Get all Mythic+ ratings for a character."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM mythic_plus
            WHERE character_id = ?
            ORDER BY season DESC
        """, (character_id,))

        rows = cursor.fetchall()

        return [dict(row) for row in rows]


def get_mythic_plus_for_character_season(character_id: int, season: str) -> Optional[Dict]:
    """Return the mythic_plus row for a specific character and season, or None if absent."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM mythic_plus
            WHERE character_id = ? AND season = ?
        """, (character_id, season))

        row = cursor.fetchone()
        return dict(row) if row else None


def get_top_mythic_plus(season: str, limit: int = 10) -> List[Dict]:
    """
    Return the top characters by Mythic+ rating for a given season.

    Args:
        season: Season identifier as stored in the DB (numeric API season ID string).
        limit: Maximum number of results to return.

    Returns:
        List of dicts with keys: name, realm, region, score, last_updated.
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.name, c.realm, c.region, mp.score, mp.last_updated
            FROM mythic_plus mp
            JOIN characters c ON mp.character_id = c.id
            WHERE mp.season = ? AND mp.score > 0
            ORDER BY mp.score DESC
            LIMIT ?
        """, (season, limit))

        rows = cursor.fetchall()

        return [dict(row) for row in rows]


# Mythic Keystone Season operations

def upsert_season(api_id: int, name: str, is_current: bool) -> None:
    """
    Insert or update a Mythic Keystone season record.

    When is_current is True, clears the is_current flag on all other rows
    before marking this season as current, ensuring only one row is ever active.
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        if is_current:
            cursor.execute("UPDATE mythic_keystone_seasons SET is_current = 0")

        cursor.execute("""
            INSERT INTO mythic_keystone_seasons (api_id, name, is_current)
            VALUES (?, ?, ?)
            ON CONFLICT(api_id) DO UPDATE SET
                name = excluded.name,
                is_current = excluded.is_current
        """, (api_id, name, 1 if is_current else 0))

        conn.commit()
        logger.debug(f"Upserted season {api_id} ({name}), is_current={is_current}")


def get_current_season() -> Optional[Dict]:
    """Return the mythic_keystone_seasons row where is_current=1, or None."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM mythic_keystone_seasons WHERE is_current = 1 LIMIT 1
        """)

        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_seasons() -> List[Dict]:
    """Return all season rows from mythic_keystone_seasons ordered by api_id ascending."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM mythic_keystone_seasons ORDER BY api_id ASC
        """)

        return [dict(row) for row in cursor.fetchall()]


def get_ended_seasons_missing_for_character(character_id: int) -> List[str]:
    """
    Return the api_id (as TEXT) of every ended season that has no mythic_plus
    record for the given character.

    Uses a LEFT JOIN so characters with zero M+ history correctly get all
    ended seasons returned (a NOT IN subquery would fail in that case).
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT CAST(s.api_id AS TEXT)
            FROM mythic_keystone_seasons s
            LEFT JOIN mythic_plus mp
                ON mp.character_id = ?
                AND mp.season = CAST(s.api_id AS TEXT)
            WHERE s.is_current = 0
              AND mp.id IS NULL
            ORDER BY s.api_id ASC
        """, (character_id,))

        return [row[0] for row in cursor.fetchall()]


def get_latest_mythic_plus_season() -> Optional[str]:
    """
    Return the season identifier (as TEXT) for the current active season.

    Prefers the mythic_keystone_seasons table. Falls back to the highest
    numeric season in mythic_plus with score > 0 for installs that predate
    the seasons table.
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT CAST(api_id AS TEXT) FROM mythic_keystone_seasons WHERE is_current = 1 LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return row[0]

        # Fallback: derive from existing mythic_plus data
        cursor.execute("""
            SELECT season
            FROM mythic_plus
            WHERE score > 0
            GROUP BY season
            ORDER BY CAST(season AS INTEGER) DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return row["season"] if row else None


# PvP operations
def upsert_pvp_rating(character_id: int, bracket: str, rating: int, season: str = None) -> None:
    """
    Insert or update PvP rating for a character.
    
    Args:
        character_id: Character ID
        bracket: PvP bracket (2v2, 3v3, RBG)
        rating: Rating value
        season: Season identifier (optional)
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO pvp (character_id, bracket, rating, season)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(character_id, bracket, season) DO UPDATE SET
                rating = excluded.rating,
                last_updated = CURRENT_TIMESTAMP
        """, (character_id, bracket.upper(), rating, season))
        
        conn.commit()
        
        logger.debug(f"Upserted {bracket} rating {rating} for character ID {character_id}")


def get_character_pvp_ratings(character_id: int) -> List[Dict]:
    """Get all PvP ratings for a character."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pvp 
            WHERE character_id = ? 
            ORDER BY bracket, season DESC
        """, (character_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


# Static lookup table operations

def upsert_class(class_id: int, name: str) -> None:
    """Insert or update a WoW playable class record."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO wow_classes (id, name) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET name = excluded.name
        """, (class_id, name))
        conn.commit()


def upsert_race(race_id: int, name: str, faction: Optional[str] = None) -> None:
    """Insert or update a WoW playable race record."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO wow_races (id, name, faction) VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name = excluded.name, faction = excluded.faction
        """, (race_id, name, faction))
        conn.commit()


def get_all_classes() -> List[Dict]:
    """Return all WoW playable classes ordered by id."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM wow_classes ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


def get_all_races() -> List[Dict]:
    """Return all WoW playable races ordered by id."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM wow_races ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]


# Database maintenance
def cleanup_old_data(days: int = 30) -> None:
    """
    Remove old records to keep database size manageable.
    
    Args:
        days: Age threshold for data cleanup
    """
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        # Clean up old recipe data (recipes don't change often)
        cursor.execute("""
            DELETE FROM recipes 
            WHERE profession_id IN (
                SELECT p.id FROM professions p
                JOIN characters c ON p.character_id = c.id
                WHERE c.last_updated < datetime('now', '-{} days')
            )
        """.format(days))
        
        conn.commit()
        
        logger.info(f"Cleaned up old data older than {days} days")


def get_database_stats() -> Dict:
    """Get database statistics."""
    with DatabaseConnection() as conn:
        cursor = conn.cursor()
        
        stats = {}
        
        # Character count
        cursor.execute("SELECT COUNT(*) FROM characters")
        stats['characters'] = cursor.fetchone()[0]
        
        # Profession count
        cursor.execute("SELECT COUNT(*) FROM professions")
        stats['professions'] = cursor.fetchone()[0]
        
        # Recipe count
        cursor.execute("SELECT COUNT(*) FROM recipes")
        stats['recipes'] = cursor.fetchone()[0]
        
        # Mythic+ ratings count
        cursor.execute("SELECT COUNT(*) FROM mythic_plus")
        stats['mythic_plus'] = cursor.fetchone()[0]
        
        # PvP ratings count
        cursor.execute("SELECT COUNT(*) FROM pvp")
        stats['pvp'] = cursor.fetchone()[0]
        
        return stats


# Initialize database on module import
init_db()

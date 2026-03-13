"""
Roster Sync Task

Populates and maintains the SQLite database with complete guild roster data
from the Battle.net API. Can be run directly from the command line or 
called programmatically.

Usage (CLI):
    python -m tasks.roster_sync

Usage (programmatic):
    from tasks.roster_sync import run_sync
    run_sync()
"""

import time
import logging
from typing import List, Dict
from configs import discord_conf
from discord_webhook import DiscordWebhook
from services import blizzard, database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Guild information
GUILD_SLUG = "drama-club"
GUILD_REALM_SLUG = "mugthol"
REGION = "us"
LOCALE = "en_US"

WEBHOOK_URL = discord_conf.WEBHOOK_URL


def run_sync() -> None:
    """Full roster sync: fetches fresh data and updates the database."""
    start_time = time.time()
    
    logger.info(f"Starting roster sync for {GUILD_SLUG} on {GUILD_REALM_SLUG}")
    
    try:
        # Fetch guild roster from Battle.net API
        roster_data = blizzard.get_guild_roster(REGION, LOCALE, GUILD_REALM_SLUG, GUILD_SLUG)
        members = roster_data.get("members", [])
        
        logger.info(f"Retrieved {len(members)} guild members from API")
        
        # Process each member
        processed_count = 0
        for member in members:
            try:
                process_member(member)
                processed_count += 1
                
                # Log progress every 10 members
                if processed_count % 10 == 0:
                    logger.info(f"Processed {processed_count}/{len(members)} members")
                    
            except Exception as e:
                character_name = member.get("character", {}).get("name", "Unknown")
                logger.error(f"Error processing member {character_name}: {e}")
                continue
        
        # Get database statistics
        stats = database.get_database_stats()
        
        elapsed_minutes = (time.time() - start_time) / 60
        success_message = (
            f"Roster Sync Successful. Processed {processed_count} members. "
            f"Execution time: {elapsed_minutes:.2f} minutes.\n"
            f"Database stats: {stats}"
        )
        logger.info(success_message)
        
        # Send notification to Discord
        if WEBHOOK_URL and WEBHOOK_URL != "[ discord webhook url ]":
            try:
                webhook = DiscordWebhook(url=WEBHOOK_URL, content=success_message)
                webhook.execute()
            except Exception as e:
                logger.warning(f"Failed to send Discord notification: {e}")
        
    except Exception as e:
        error_message = f"Roster Sync Failed: {e}"
        logger.error(error_message)
        
        # Send error notification to Discord
        if WEBHOOK_URL and WEBHOOK_URL != "[ discord webhook url ]":
            try:
                webhook = DiscordWebhook(url=WEBHOOK_URL, content=error_message)
                webhook.execute()
            except Exception as ex:
                logger.warning(f"Failed to send Discord error notification: {ex}")
        
        raise


def process_member(member: Dict) -> None:
    """
    Process a single guild member and update database records.
    
    Args:
        member: Member data from Battle.net API
    """
    character_data = member.get("character", {})
    character_name = character_data.get("name", "").lower()
    realm_slug = character_data.get("realm", {}).get("slug", "")
    
    if not character_name or not realm_slug:
        logger.warning(f"Skipping member with missing character data: {member}")
        return
    
    # Extract rank information (integer in Blizzard API)
    rank = member.get("rank", 0) if isinstance(member.get("rank"), int) else 0
    
    # Extract faction information
    faction_data = character_data.get("faction", {})
    faction = faction_data.get("type") if isinstance(faction_data, dict) else None
    
    # Extract race and class IDs
    race_id = character_data.get("playable_race", {}).get("id") if isinstance(character_data.get("playable_race"), dict) else None
    class_id = character_data.get("playable_class", {}).get("id") if isinstance(character_data.get("playable_class"), dict) else None
    
    # Extract class name for readability
    class_name = character_data.get("playable_class", {}).get("name", "") if isinstance(character_data.get("playable_class"), dict) else ""
    
    # Upsert character record
    character_id = database.upsert_character(
        name=character_name,
        realm=realm_slug,
        region=REGION,
        level=character_data.get("level"),
        faction=faction,
        rank=rank,
        race_id=race_id,
        class_id=class_id
    )
    
    # Fetch and process character professions
    try:
        process_character_professions(character_id, character_name, realm_slug)
    except Exception as e:
        logger.error(f"Error processing professions for {character_name}: {e}")


def process_character_professions(character_id: int, character_name: str, realm_slug: str) -> None:
    """
    Fetch and process character professions from Battle.net API.
    
    Args:
        character_id: Database character ID
        character_name: Character name
        realm_slug: Realm slug
    """
    # Fetch character professions from Battle.net API
    try:
        professions_data = blizzard.get_character_professions(REGION, LOCALE, realm_slug, character_name)
    except Exception as e:
        # Handle 404 errors specifically - this usually means the character has no professions
        if "404" in str(e):
            logger.info(f"Character {character_name} has no professions (404 response from API)")
            return
        else:
            # Re-raise any other exceptions
            raise
    
    # Process primary professions
    primaries = professions_data.get("primaries", [])
    for primary in primaries:
        profession_data = primary.get("profession", {})
        profession_name = profession_data.get("name", "").lower()
        
        if not profession_name:
            continue
            
        # Get profession tiers
        tiers = primary.get("tiers", [])
        max_tier = tiers[-1] if tiers else {}
        skill_level = max_tier.get("skill_points", 0)
        max_skill_level = max_tier.get("max_skill_points", 0)
        
        # Upsert profession record
        profession_id = database.upsert_profession(
            character_id=character_id,
            name=profession_name,
            skill_level=skill_level,
            max_skill_level=max_skill_level
        )
        
        # Process known recipes
        known_recipes = []
        for tier in tiers:
            recipes = tier.get("known_recipes", [])
            for recipe in recipes:
                known_recipes.append({
                    "name": recipe.get("name", ""),
                    "category": tier.get("tier", {}).get("name", "")
                })
        
        # Add recipes to database
        database.add_recipes(profession_id, known_recipes)


if __name__ == "__main__":
    run_sync()

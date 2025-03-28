from configs import blizz_conf, redis_conf
import json

r = redis_conf.r
api_client = blizz_conf.api_client

def delete_redis_key(prefix):
    """Delete keys nested in a redis tree"""
    for key in r.keys(prefix):
        print("deleting " + key)
        r.delete(key)
    return

def guild_roster_update( region, locale, guild_slug, guild_realm_slug ):
    """Retrieves guild roster information as json output from battle.net's world of warcraft profile api and caches it to redis"""
    guild_info = api_client.wow.profile.get_guild_roster( region, locale, guild_realm_slug, guild_slug )
    r.set( "guild_roster", json.dumps( guild_info ) )
    return

def character_professions_update( character_realm_slug, character_name_lower ):
    """Retrieves character profession information as json output from battle.net's world of warcraft profile api and caches it to redis"""
    try:
        character_professions = api_client.wow.profile.get_character_professions_summary( 'us', 'en_us', character_realm_slug, character_name_lower )
        r.set( "player_professions: " + character_name_lower + "+" + character_realm_slug, json.dumps( character_professions ) )
    except:
        print( "Error updating " + character_name_lower + "+" + character_realm_slug ) 
    return 

def guild_roster_character_professions_update( guild_roster ):
    """Loops through an entire guild roster calling character_professions_update()"""
    for member in guild_roster:
        try:
            character_name = member.get( "character" ).get( "name" ).lower()
            character_realm_slug = member.get( "character" ).get( "realm" ).get( "slug" )
            print( "updating " + character_name.lower() + "+" + character_realm_slug )
            character_professions_update( character_realm_slug, character_name )
        except:
            print( "Error updating " + character_name.lower() + "+" + character_realm_slug ) 
    return


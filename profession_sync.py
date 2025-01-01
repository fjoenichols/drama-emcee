from configs import redis_conf
import json, time, caching

guild_slug = 'drama-club'
guild_realm_slug = "mugthol"

start_time = time.time()

print("clearing guild_roster cache")
caching.delete_redis_key("guild_roster")

print("clearing player_professions cache")
caching.delete_redis_key("player_professions:*")

print("clearing professions cache")
caching.delete_redis_key("professions:*")

print("getting roster for " + guild_slug + " " + guild_realm_slug)
caching.guild_roster_update('us', 'en_US', guild_slug, guild_realm_slug)
guild_roster = json.loads( redis_conf.r.get( "guild_roster" ) ).get( "members" )

print("getting character profession updates for " + guild_slug + " " + guild_realm_slug)
caching.guild_roster_character_professions_update(guild_roster)

for character in guild_roster:
    try: 
        character_name_lower = character.get("character").get("name").lower() 
        character_realm_slug = character.get("character").get("realm").get("slug")

        p = character_name_lower + "+" + character_realm_slug
        print(p)

        player = json.loads( redis_conf.r.get( "player_professions: " + p ) )

        for primary_profession in player.get("primaries"):

            # make profession lists
            profession = primary_profession.get("profession").get("name").lower()
            profession_path = "professions: "

            print(profession)
            if redis_conf.r.get(profession_path):
                if p in redis_conf.r.get(profession_path):
                    print (p + " already present in " + profession + " list.")
                else:
                    redis_conf.r.append(profession_path, p + " ")  
                    print (p + " added to" + profession + " list.")
            else:
                redis_conf.r.set(profession_path, p + " ")
                print (p + " added to newly created " + profession + " list.")

            # make profession tier lists
            for tier in primary_profession.get("tiers"):
                profession_tier = tier.get("tier").get("name").lower()
                profession_tier_path = profession_path + "tier: " + profession_tier

                print(profession_tier)
                if redis_conf.r.get(profession_tier):
                    if p in redis_conf.r.get(profession_tier_path):
                        print (p + " already present in " + profession_tier + " list.")
                    else:
                        redis_conf.r.append(profession_tier_path, p + " ")  
                        print (p + " added to " + profession_tier + " list.")
                else:
                    redis_conf.r.set(profession_tier_path, p + " ")
                    print (p + " added to newly created " + profession_tier + " list.")

                # make recipe lists
                for recipe in tier.get("known_recipes"):
                    profession_recipe = recipe.get("name").lower()
                    profession_recipe_path = "professions: recipes: " + profession_recipe

                    print(profession_recipe)
                    if redis_conf.r.get(profession_recipe_path):
                        if p in redis_conf.r.get(profession_recipe_path):
                            print (p + " already present in " + profession_recipe + " list.")
                        else:
                            redis_conf.r.append(profession_recipe_path, p + " ")
                            print (p + " added to " + profession_recipe + " list.")
                    else:
                        redis_conf.r.set(profession_recipe_path, p + " ")
                        print (p + " added to newly created " + profession_recipe + " list.")
    except: 
        errorcatch_path = "profession_errorcatch"

end_time = time.time()

execution_time = (end_time - start_time)/60 
print("Execution time: " + str(execution_time) + " minutes.")
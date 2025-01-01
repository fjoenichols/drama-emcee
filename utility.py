from configs import redis_conf
import json, random

r = redis_conf.r

def who_knows_recipe( recipe ):
    """Retrieves a list of players who know a specific recipe"""
    try:
        crafters = r.get( "professions: recipes: " + recipe )
        c_list = crafters_list(crafters)

        return "The following players know **" + recipe.title() + "**\n\n" + c_list
    except: 
        return "Nobody in the guild knows **" + recipe.title() + "**."

def crafters_list( crafters ):
        crafters_array = crafters.split(" ")
        crafters_array = crafters_array[:-1]
        c = []

        for crafter in crafters_array:
            player_name = crafter.split("+")[0]
            player_realm = crafter.split("+")[1]
            proper_name = json.loads( redis_conf.r.get("player_professions: " + player_name + "+" + player_realm) ).get("character").get("name")
            proper_realm = json.loads( redis_conf.r.get("player_professions: " + player_name + "+" + player_realm) ).get("character").get("realm").get("name")

            c.append(proper_name + "-" + proper_realm)

        return ", ".join(c)

def roll( d ):
    return random.randint( 1, d )

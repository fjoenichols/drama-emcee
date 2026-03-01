"""
Example Blizzard Battle.net API config.
Copy this file to configs/blizz_conf.py and fill in your credentials.
"""

from blizzardapi2 import BlizzardApi

api_client = BlizzardApi("[ battle.net client id ]", "[ battle.net client secret ]")

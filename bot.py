from configs import redis_conf, discord_conf
import discord, utility
from discord.ext import commands
from discord import Interaction

r = redis_conf.r

def run_discord_bot():
    TOKEN = discord_conf.TOKEN
    intents = discord.Intents.all()
    intents.message_content = True
    client = commands.Bot( command_prefix='.', description='Retrieves guild roster information as json output from battle.net\'s world of warcraft profile api and caches it to redis', intents=intents)

    @client.event
    async def on_ready():
        await client.tree.sync()
        await client.change_presence(activity=discord.activity.Game(name="World of Warcraft"))
        print( f'{ client.user.name } just showed up!' )

    @client.tree.command(name="ping", description="show ping")
    async def ping( interaction : Interaction ):
        bot_latency = round( client.latency*1000 )
        await interaction.response.send_message(f"Pong!... {bot_latency} ms")

    @client.tree.command(name="roll", description="roll a die with 'd' sides")
    async def roll( interaction : Interaction, d: int ):
        await interaction.response.send_message( f"{ interaction.user } rolled a d{ d } and got a { utility.roll( d ) }" )

    @client.tree.command(name="who_knows_recipe", description="search which guild members know a specific recipe")
    async def who_knows_recipe( interaction : Interaction, recipe: str ):
        recipe = recipe.lower()
        await interaction.response.send_message(utility.who_knows_recipe( recipe ))

    client.run(TOKEN)
from configs import redis_conf, discord_conf
import discord, caching, json, utility, retrieval, typing
from discord.ext import commands
from discord import app_commands
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

    @client.tree.command(name="who_knows_profession", description="search which guild members know a specific profession")
    async def who_knows_profession( interaction : Interaction, profession: str ):
        profession = profession.lower()
        await interaction.response.send_message(retrieval.who_knows_profession( profession ))

    @client.tree.command(name="who_knows_recipe", description="search which guild members know a specific recipe")
    async def who_can_craft( interaction : Interaction, recipe: str ):
        recipe = recipe.lower()
        await interaction.response.send_message(retrieval.who_knows_recipe( recipe ))

    @who_knows_profession.autocomplete("profession")
    async def profession_autocompletion(
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        professions_list = r.get( "game-data: professions-list" ).split(",")
        data = []
        for profession_choice in professions_list:
            if current.lower() in profession_choice.lower():
                data.append(app_commands.Choice(name=profession_choice, value=profession_choice))
        return data

    client.run(TOKEN)
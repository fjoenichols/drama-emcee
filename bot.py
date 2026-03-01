"""
Bot entry point — initialises the Discord client and loads all Cogs.

To add a new feature, create a new file in cogs/ with a setup(bot) coroutine
and add its module path to the COGS list below.
"""

import discord
from discord.ext import commands
from configs import discord_conf

TOKEN = discord_conf.TOKEN

# ---------------------------------------------------------------------------
# Cog registry — add new feature modules here
# ---------------------------------------------------------------------------
COGS = [
    "cogs.general",
    "cogs.professions",
]


async def _load_cogs(bot: commands.Bot) -> None:
    """Load all Cog extensions registered in the COGS list."""
    for cog in COGS:
        await bot.load_extension(cog)
        print(f"  loaded cog: {cog}")


def run_discord_bot() -> None:
    """Initialise and run the Discord bot until interrupted."""
    intents = discord.Intents.all()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix=".",
        description=(
            "Drama Club guild bot — queries guild roster, professions, and "
            "recipe data via the Battle.net API."
        ),
        intents=intents,
    )

    @bot.event
    async def on_ready() -> None:
        print(f"\nLoading cogs...")
        await _load_cogs(bot)
        await bot.tree.sync()
        await bot.change_presence(activity=discord.activity.Game(name="World of Warcraft"))
        print(f"\n{bot.user.name} just showed up!")

    bot.run(TOKEN)

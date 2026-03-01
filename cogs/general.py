"""
General Cog — miscellaneous guild-utility commands.

Commands:
  /ping  — show bot latency
  /roll  — roll a die with d sides
"""

import random
from discord.ext import commands
from discord import Interaction, app_commands


class GeneralCog(commands.Cog, name="General"):
    """Miscellaneous utility commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Store a reference to the bot instance."""
        self.bot = bot

    @app_commands.command(name="ping", description="Show bot latency")
    async def ping(self, interaction: Interaction) -> None:
        """Respond with the bot's current round-trip latency in milliseconds."""
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong!... {latency_ms} ms")

    @app_commands.command(name="roll", description="Roll a die with 'd' sides")
    async def roll(self, interaction: Interaction, d: int) -> None:
        """Roll a d-sided die and post the result to the channel."""
        result = random.randint(1, d)
        await interaction.response.send_message(
            f"{interaction.user} rolled a d{d} and got a {result}"
        )


async def setup(bot: commands.Bot) -> None:
    """Register the GeneralCog with the bot."""
    await bot.add_cog(GeneralCog(bot))

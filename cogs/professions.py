"""
Professions Cog — commands related to WoW crafting professions.

Commands:
  /who_knows_recipe  — search which guild members know a specific recipe
"""

from discord.ext import commands
from discord import Interaction, app_commands
from services import professions as profession_service


class ProfessionsCog(commands.Cog, name="Professions"):
    """Commands for querying guild profession and recipe data."""

    def __init__(self, bot: commands.Bot) -> None:
        """Store a reference to the bot instance."""
        self.bot = bot

    @app_commands.command(
        name="who_knows_recipe",
        description="Search which guild members know a specific recipe",
    )
    async def who_knows_recipe(self, interaction: Interaction, recipe: str) -> None:
        """Look up and display all guild members who know the requested recipe."""
        result = profession_service.who_knows_recipe(recipe.lower())
        await interaction.response.send_message(result)


async def setup(bot: commands.Bot) -> None:
    """Register the ProfessionsCog with the bot."""
    await bot.add_cog(ProfessionsCog(bot))

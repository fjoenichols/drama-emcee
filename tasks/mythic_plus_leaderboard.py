"""
Mythic Plus Leaderboard Task

Queries the database for the top 10 guild members by Mythic+ rating for the
most recently active season and posts the results to the configured Discord
webhook.

Intended to run nightly via cron after mythic_plus_ratings has completed.

Usage (CLI):
    python -m tasks.mythic_plus_leaderboard
"""

import logging

from configs import discord_conf
from discord_webhook import DiscordWebhook
from services import database

WEBHOOK_URL = discord_conf.LEADERBOARD_WEBHOOK_URL
TOP_N = 20

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _format_leaderboard(season: str, rows: list[dict]) -> str:
    """Format the top-N results into a Discord message string."""
    lines = [f"**Mythic+ Leaderboard — {season}**\n"]
    for rank, row in enumerate(rows, start=1):
        name = row["name"].title()
        realm = row["realm"].replace("-", " ").title()
        score = row["score"]
        lines.append(f"`{rank:>2}.` **{name}** ({realm}) — {score:.1f}")
    return "\n".join(lines)


def run() -> None:
    """Post the top 20 M+ ratings for the current active season to Discord."""
    season_row = database.get_current_season()
    if season_row is None:
        print("No season data found in the database. Run mythic_plus_ratings first.")
        return

    season_id_str = str(season_row["api_id"])
    season_name = season_row["name"]

    rows = database.get_top_mythic_plus(season=season_id_str, limit=TOP_N)
    if not rows:
        print(f"No scores > 0 found for {season_name}.")
        return

    message = _format_leaderboard(season_name, rows)
    print(message)

    if not WEBHOOK_URL or WEBHOOK_URL == "[ leaderboard discord webhook url ]":
        print("\n(Discord webhook not configured — skipping post.)")
        return

    try:
        webhook = DiscordWebhook(url=WEBHOOK_URL, content=message)
        response = webhook.execute()
        print(f"\nPosted to Discord (status {response.status_code}).")
    except Exception as e:
        logger.error(f"Failed to post leaderboard to Discord: {e}")
        raise


if __name__ == "__main__":
    run()

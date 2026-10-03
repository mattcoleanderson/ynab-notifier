import discord

from ynab_notifier.budget import BudgetBot
from ynab_notifier.config import Config


def main() -> None:
    config = Config.from_env()


    bot = BudgetBot()


    @bot.tree.command(name='budget-remaining', description='Show remaining budget')
    async def budget(interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Hello, world!')

    bot.run(config.discord_token)

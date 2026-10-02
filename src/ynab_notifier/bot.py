import discord
from discord.ext import commands

from ynab_notifier.config import Config

class HelloBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            help_command=None,
        )

    async def setup_hook(self) -> None:
        await self.tree.sync()


def main() -> None:
    config = Config.from_env()


    bot = HelloBot()

    @bot.tree.command(name='hello', description='Say hello')
    async def hello(interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Hello, world!')

    bot.run(config.discord_token)

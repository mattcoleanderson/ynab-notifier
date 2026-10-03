
import discord
from discord.ext import commands


class BudgetBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            help_command=None,
        )

    async def setup_hook(self) -> None:
        await self.tree.sync()


import discord
from discord.ext import commands


class BudgetCommands(commands.Cog):
    @discord.app_commands.command(
        name="budget-remaining",
        description="Show remaining budget",
    )
    async def budget_remaining(
        self,
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.send_message("Hello, world!")


class BudgetBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            help_command=None,
        )

    async def setup_hook(self) -> None:
        await self.add_cog(BudgetCommands())
        await self.tree.sync()

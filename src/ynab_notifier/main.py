from ynab_notifier.bot import BudgetBot
from ynab_notifier.config import Config
from ynab_notifier.ynab_client import YNABClient


def main() -> None:
    config = Config.from_env()

    ynab = YNABClient(config.ynab_token, config.budget_id)


    bot = BudgetBot()
    bot.run(config.discord_token)

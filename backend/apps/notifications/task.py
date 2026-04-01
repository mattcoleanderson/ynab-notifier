from celery import shared_task

from apps.notifications.services.discord import DiscordService
from apps.notifications.services.ynab import YNABClient
from config.app_settings import settings


@shared_task
def send_daily_notification():
    client = YNABClient(access_token=settings.YNAB_TOKEN, budget_id=settings.BUDGET_ID)
    categories = client.get_categories_by_id(settings.CATEGORY_IDS)

    if categories is None:
        return False

    discord = DiscordService(webhook_url=settings.DISCORD_WEBHOOK_URL)
    message = discord.format_message(categories)
    return discord.send("", message)

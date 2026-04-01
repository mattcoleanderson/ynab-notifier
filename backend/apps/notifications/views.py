from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from apps.notifications.services.discord import DiscordService
from apps.notifications.services.ynab import YNABClient
from config.app_settings import settings


@api_view(["GET"])
def get_ynab_categories(request):
    client = YNABClient(access_token=settings.YNAB_TOKEN, budget_id=settings.BUDGET_ID)
    categories = client.get_categories_by_id(settings.CATEGORY_IDS)

    if categories is None:
        return Response({"error": "Category not found"}, status.HTTP_404_NOT_FOUND)

    return Response([c.to_dict() for c in categories])


@api_view(["GET"])
def send_test_notification(request):
    client = YNABClient(access_token=settings.YNAB_TOKEN, budget_id=settings.BUDGET_ID)
    categories = client.get_categories_by_id(settings.CATEGORY_IDS)

    if categories is None:
        return Response({"error": "Categories not found"}, status.HTTP_404_NOT_FOUND)

    discord = DiscordService(webhook_url=settings.DISCORD_WEBHOOK_URL)
    message = discord.format_message(categories)
    sent = discord.send("", message)

    if not sent:
        return Response(
            {"error": "Failed to send notification"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({"message": "Notification sent"})

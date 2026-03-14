from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from apps.notifications.services.sms import SMSService
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
    # client = YNABClient(access_token=settings.YNAB_TOKEN, budget_id=settings.BUDGET_ID)

    sms = SMSService(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
        settings.TWILIO_FROM_NUMBER,
    )

    isSent = sms.send_message(settings.TWILIO_TO_NUMBER, "Hello, World!")

    if not isSent:
        return Response(
            {"error": "Failed to send SMS"}, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({"message": "Notification sent", "to": settings.TWILIO_TO_NUMBER, "from": settings.TWILIO_FROM_NUMBER})

from django.urls import path

from .views import get_ynab_categories, send_test_notification

urlpatterns = [
    path("category/", get_ynab_categories, name="Get YNAB Categories"),
    path("send/", send_test_notification, name="Send Test Notification"),

]

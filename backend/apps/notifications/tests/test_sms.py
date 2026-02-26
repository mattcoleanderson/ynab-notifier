
from datetime import date
import pytest
from apps.notifications.services.sms import SMSService


def test_format_message(category_grocery, category_dining_out, category_shopping):
    categories = [
            category_grocery,
            category_dining_out,
            category_shopping,
    ]

    smsService = SMSService()
    result = smsService.format_message(categories)


    today = date.today().strftime("%a, %b %d")
    expected = (
        f"Daily Budget Update ({today}):\n"
        "\n"
        "Groceries:   $252.50 remaining\n"
        "Dining Out:  $111.00 remaining\n"
        "Shopping:    $ 62.30 remaining\n"
        "──────────────────────────────\n"
        "Total:       $425.80 remaining"
    )

    assert result == expected 

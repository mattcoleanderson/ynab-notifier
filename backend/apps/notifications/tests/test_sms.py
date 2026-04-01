from datetime import date

from pytest_mock import MockFixture, MockerFixture
from twilio.base.exceptions import TwilioRestException
from apps.notifications.services.sms import SMSService


def test_send_returns_true_on_success(mocker: MockerFixture):
    phone_num = "5019529943"
    message = "Hello, World!"

    smsService = SMSService(
        account_sid="123",
        auth_token="456",
        from_number="1111",
    )

    mocker.patch("apps.notifications.services.sms.Client")

    result = smsService.send(phone_num, message)

    assert result == True


def test_send_returns_false_on_failure(mocker: MockFixture):
    phone_num = ""
    message = "Hello, World!"

    smsService = SMSService(
        account_sid="123",
        auth_token="456",
        from_number="",
    )

    mock_client = mocker.patch("apps.notifications.services.sms.Client")
    mock_client.return_value.messages.create.side_effect = TwilioRestException(
        400, "uri"
    )

    result = smsService.send(phone_num, message)

    assert result == False


def test_format_message(category_grocery, category_dining_out, category_shopping):
    categories = [
        category_grocery,
        category_dining_out,
        category_shopping,
    ]

    smsService = SMSService("", "", "")
    result = smsService.format_message(categories)

    today = date.today().strftime("%a, %b %d")
    expected = (
        f"Budget Left ({today}):\n"
        "\n"
        "Groceries:   $252.50\n"
        "Dining Out:  $111.00\n"
        "Shopping:    $ 62.30\n"
        "─────────────────────\n"
        "Total:        $425.80"
    )

    assert result == expected

from pytest_mock import MockerFixture

from apps.notifications.tasks import send_daily_notification


def test_send_daily_notification_sends_message(
    mocker: MockerFixture, category_grocery, category_dining_out
):
    mocker.patch(
        "apps.notifications.tasks.YNABClient.get_categories_by_id",
        return_value=[category_grocery, category_dining_out],
    )
    mock_send = mocker.patch(
        "apps.notifications.tasks.DiscordService.send",
        return_value=True,
    )
    mock_format = mocker.patch(
        "apps.notifications.tasks.DiscordService.format_message",
        return_value="formatted message",
    )

    result = send_daily_notification()

    assert result is True
    mock_format.assert_called_once_with([category_grocery, category_dining_out])
    mock_send.assert_called_once_with("", "formatted message")


def test_send_daily_notification_returns_false_when_categories_not_found(
    mocker: MockerFixture,
):
    mocker.patch(
        "apps.notifications.tasks.YNABClient.get_categories_by_id",
        return_value=None,
    )

    result = send_daily_notification()

    assert result is False


def test_send_daily_notification_returns_false_when_send_fails(
    mocker: MockerFixture, category_grocery
):
    mocker.patch(
        "apps.notifications.tasks.YNABClient.get_categories_by_id",
        return_value=[category_grocery],
    )
    mocker.patch(
        "apps.notifications.tasks.DiscordService.format_message",
        return_value="formatted message",
    )
    mocker.patch(
        "apps.notifications.tasks.DiscordService.send",
        return_value=False,
    )

    result = send_daily_notification()

    assert result is False

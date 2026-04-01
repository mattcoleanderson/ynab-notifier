from pytest_mock import MockerFixture
from requests.exceptions import RequestException

from apps.notifications.services.discord import DiscordService


def test_send_returns_true_on_success(mocker: MockerFixture):
    mock_post = mocker.patch("apps.notifications.services.discord.requests.post")
    mock_post.return_value.status_code = 204

    service = DiscordService(webhook_url="https://discord.com/api/webhooks/fake")
    result = service.send("", "Hello, World!")

    assert result is True
    mock_post.assert_called_once_with(
        "https://discord.com/api/webhooks/fake",
        json={"content": "Hello, World!"},
    )


def test_send_returns_false_on_failure(mocker: MockerFixture):
    mock_post = mocker.patch("apps.notifications.services.discord.requests.post")
    mock_post.return_value.status_code = 400

    service = DiscordService(webhook_url="https://discord.com/api/webhooks/fake")
    result = service.send("", "Hello, World!")

    assert result is False


def test_send_returns_false_on_exception(mocker: MockerFixture):
    mock_post = mocker.patch("apps.notifications.services.discord.requests.post")
    mock_post.side_effect = RequestException("Connection error")

    service = DiscordService(webhook_url="https://discord.com/api/webhooks/fake")
    result = service.send("", "Hello, World!")

    assert result is False

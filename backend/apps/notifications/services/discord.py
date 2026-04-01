from typing import List

import requests
from requests.exceptions import RequestException
from ynab import Category

from apps.notifications.services.base import NotificationService


class DiscordService(NotificationService):

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    # TODO: Emojis render as 2 columns in Discord code blocks but grapheme.length
    # counts them as 1. The Total line padding currently assumes emojis are present,
    # so alignment breaks for users without emojis in their category names.
    def format_message(self, categories: List[Category]) -> str:
        message = super().format_message(categories)
        return f"```\n{message}\n```"

    def send(self, recipient: str, message: str) -> bool:
        try:
            response = requests.post(
                self.webhook_url,
                json={"content": message},
            )
            return response.status_code == 204
        except RequestException as e:
            print("Exception when calling Discord webhook: %s\n" % e)
            return False

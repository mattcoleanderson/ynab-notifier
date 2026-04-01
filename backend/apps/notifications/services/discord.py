import requests
from requests.exceptions import RequestException

from apps.notifications.services.base import NotificationService


class DiscordService(NotificationService):

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

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

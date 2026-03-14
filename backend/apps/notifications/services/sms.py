from twilio.base.exceptions import TwilioRestException
from twilio.rest.api.v2010.account.message import MessageInstance
from twilio.rest import Client

from apps.notifications.services.base import NotificationService


class SMSService(NotificationService):

    def __init__(self, account_sid: str, auth_token: str, from_number: str) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send(self, recipient: str, message: str) -> bool:
        client = Client(self.account_sid, self.auth_token)

        try:
            _response: MessageInstance = client.messages.create(
                to=recipient, from_=self.from_number, body=message
            )
            return True
        except TwilioRestException as e:
            print("Exception when calling Twilio->messages.create: %s\n" % e)
            return False

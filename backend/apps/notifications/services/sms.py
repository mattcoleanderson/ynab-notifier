from datetime import date
from decimal import Decimal
from typing import List
from twilio.base.exceptions import TwilioRestException
from twilio.rest.api.v2010.account.message import MessageInstance
from ynab import Category
from twilio.rest import Client


def to_dollars(milliunits: int) -> Decimal:
    return Decimal(milliunits) / 1000


class SMSService:

    def __init__(self, account_sid: str, auth_token: str, from_number: str) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send_message(self, to_number: str, message: str) -> bool:
        client = Client(self.account_sid, self.auth_token)


        try:
            message: MessageInstance = client.messages.create(
                to=to_number,
                from_=self.from_number,
                body=message
            )
            return True
        except TwilioRestException as e:
            print("Exception when calling Twilio->message.create: %s\n" % e)
            return False



    def format_message(self, categories: List[Category]) -> str:
        today = date.today().strftime("%a, %b %d")  # ex. Mon, Feb 14
        message = f"Daily Budget Update ({today}):\n\n"

        amounts = [to_dollars(c.goal_target + c.activity) for c in categories]
        total = sum(amounts)

        max_name_len = max(max(len(c.name) for c in categories), len("Total"))
        max_amount_len = max(len(f"{a:.2f}") for a in amounts + [total])

        # Loop through cateogries and add them as a line in message
        for i in range(len(categories)):
            name = f"{categories[i].name}:".ljust(max_name_len + 2)
            message += f"{name} ${amounts[i]:>{max_amount_len}.2f} remaining\n"

        message += "─" * (max_name_len + max_amount_len + 14) + "\n"
        name = "Total:".ljust(max_name_len + 2)
        message += f"{name} ${total:>6.2f} remaining"

        print(message)

        return message

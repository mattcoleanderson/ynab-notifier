from datetime import date
from decimal import Decimal
from typing import List
from ynab import Category


def to_dollars(milliunits: int) -> Decimal:
    return Decimal(milliunits) / 1000


class SMSService:

    def __init__(self) -> None:
        super().__init__()

    def format_message(self, categories: List[Category]) -> str:
        today = date.today().strftime("%a, %b %d")  # ex. Mon, Feb 14
        message = f"Daily Budget Update ({today}):\n\n"

        # Loop through cateogries and add them as a line in message
        for c in categories:
            amount = to_dollars(c.goal_target + c.activity)
            message += f"{c.name}: ${amount:.2f} remaining\n"

        print(message)

        return message

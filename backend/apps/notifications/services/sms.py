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

        max_name_len = max(max(len(c.name) for c in categories), len("Total"))
        total = Decimal(0)

        # Loop through cateogries and add them as a line in message
        for c in categories:
            amount = to_dollars(c.goal_target + c.activity)
            total += amount
            name = f"{c.name}:".ljust(max_name_len + 2)
            message += f"{name} ${amount:>6.2f} remaining\n"

        message += "──────────\n"
        name = "Total:".ljust(max_name_len + 2)
        message += f"{name} ${total:>6.2f} remaining"

        print(message)

        return message

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

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import List

import grapheme
from ynab import Category


def to_dollars(milliunits: int) -> Decimal:
    return Decimal(milliunits) / 1000


def visual_ljust(s: str, width: int) -> str:
    return s + " " * (width - grapheme.length(s))


class NotificationService(ABC):

    @abstractmethod
    def send(self, recipient: str, message: str) -> bool: ...

    def format_message(self, categories: List[Category]) -> str:
        today = date.today().strftime("%a, %b %d")  # ex. Mon, Feb 14
        message = f"Budget Left ({today}):\n\n"

        # goal_target is treated as 0 if there is no goal set.
        # this means that if there is any activity on this category
        # it will be negative
        amounts = [to_dollars((c.goal_target or 0) + c.activity) for c in categories]
        total = sum(amounts)

        max_name_len = max(
            max(grapheme.length(c.name) for c in categories), len("Total")
        )
        max_amount_len = max(len(f"{a:,.2f}") for a in amounts + [total])

        # Loop through cateogries and add them as a line in message
        for i in range(len(categories)):
            name = visual_ljust(f"{categories[i].name}:", max_name_len + 2)
            message += f"{name} ${amounts[i]:>{max_amount_len},.2f}\n"

        message += "─" * (max_name_len + max_amount_len + 5) + "\n"
        name = visual_ljust("Total:", max_name_len + 3)
        message += f"{name} ${total:>{max_amount_len},.2f}"

        print(message)

        return message

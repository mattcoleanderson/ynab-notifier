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


def calculate_remaining(category: Category) -> Decimal:
    if category.goal_snoozed_at is not None:
        return to_dollars(category.budgeted + category.activity)
    else:
        return to_dollars(max(category.goal_target or 0, category.budgeted) + category.activity)


class NotificationService(ABC):

    @abstractmethod
    def send(self, recipient: str, message: str) -> bool: ...

    def format_message(self, categories: List[Category]) -> str:
        today = date.today().strftime("%a, %b %d")  # ex. Mon, Feb 14
        message = f"Budget Left ({today}):\n\n"

        amounts = [calculate_remaining(c) for c in categories]
        total = sum(amounts)

        positive = [(c, a) for c, a in zip(categories, amounts) if a >= 0]
        overspent = [(c, a) for c, a in zip(categories, amounts) if a < 0]

        max_name_len = max(
            max(grapheme.length(c.name) for c in categories), len("Total")
        )
        max_amount_len = max(len(f"{a:,.2f}") for a in amounts + [total])

        separator = "─" * (max_name_len + max_amount_len + 5) + "\n"

        for c, a in positive:
            name = visual_ljust(f"{c.name}:", max_name_len + 2)
            message += f"{name} ${a:>{max_amount_len},.2f}\n"

        message += separator

        if overspent:
            for c, a in overspent:
                name = visual_ljust(f"{c.name}:", max_name_len + 2)
                message += f"{name} ${a:>{max_amount_len},.2f}\n"
            message += separator

        name = visual_ljust("Total:", max_name_len + 3)
        message += f"{name} ${total:>{max_amount_len},.2f}"

        print(message)

        return message

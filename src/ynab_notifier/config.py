from dataclasses import dataclass
import os
from typing import Self


@dataclass(frozen=True)
class Config:
    discord_token: str
    ynab_token: str
    budget_id: str
    category_ids: tuple[str, ...]

    @classmethod
    def from_env(cls) -> Self:
        return cls(
            discord_token=os.environ["DISCORD_TOKEN"],
            ynab_token=os.environ["YNAB_TOKEN"],
            budget_id=os.environ["BUDGET_ID"],
            category_ids=tuple(os.environ["CATEGORY_IDS"].split(",")),
        )

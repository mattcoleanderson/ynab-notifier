from dataclasses import dataclass
import os
from typing import Self


@dataclass(frozen=True)
class Config:
    ynab_token: str
    budget_id: str
    category_ids: tuple[str, ...]

    @classmethod
    def from_env(cls) -> Self:
        return cls(
            ynab_token=os.environ["YNAB_TOKEN"],
            budget_id=os.environ["YNAB_TOKEN"],
            category_ids=tuple(os.environ["CATEGORY_IDS"].split(",")),
        )

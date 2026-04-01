from ynab import Category


def make_category(**overrides):
    defaults = {
        "id": "test-id",
        "name": "Test Category",
        "category_group_id": "group-1",
        "hidden": False,
        "deleted": False,
        "budgeted": 0,
        "activity": 0,
        "balance": 0,
        "goal_target": None,
    }

    defaults.update(overrides)
    return Category(**defaults)

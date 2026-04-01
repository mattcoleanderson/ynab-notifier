import pytest
from apps.notifications.tests.factories import make_category


@pytest.fixture
def category_grocery():
    return make_category(
        id="aaa", name="Groceries", goal_target=500000, activity=-247500
    )


@pytest.fixture
def category_dining_out():
    return make_category(
        id="bbb", name="Dining Out", goal_target=100000, activity=--11000
    )


@pytest.fixture
def category_shopping():
    return make_category(
        id="ccc", name="Shopping", goal_target=220000, activity=-157700
    )

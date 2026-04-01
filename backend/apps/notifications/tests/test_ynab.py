from pytest_mock import MockerFixture
from ynab import Category, CategoryResponse, CategoryResponseData

from apps.notifications.services.ynab import YNABClient


def test_get_category_by_id(mocker: MockerFixture):
    category = Category(
        id="123",
        category_group_id="group-1",
        name="Groceries",
        hidden=False,
        deleted=False,
        budgeted=5000000,
        activity=4500000,
        balance=500000,
        goal_target=5000000,
    )
    response = CategoryResponse(
        data=CategoryResponseData(category=category)
    )

    mocker.patch(
        "ynab.CategoriesApi.get_category_by_id",
        return_value=response,
    )

    client = YNABClient(access_token="fake", budget_id="fake")
    category = client.get_category_by_id(category_id="123")

    print(category)

    assert category.id == "123"
    assert category.name == "Groceries"
    assert category.budgeted == 5000000
    assert category.activity == 4500000
    assert category.balance == 500000
    assert category.goal_target == 5000000


# def test_filter_ynab_category_data():
#     all_categories = [
#         { "name": "Groceries", "remaining": 252.50 },
#         { "name": "Gas", "remaining": 89.22 },
#         { "name": "Spending", "remaining": 0.00},
#     ]

from ynab import ApiClient, CategoriesApi, Category, CategoryResponse, Configuration


class YNABClient:

    def __init__(self, access_token: str, budget_id: str):
        self.config = Configuration(access_token=access_token)
        self.budget_id = (
            budget_id if budget_id else "last-used"
        )  # could be 'default' but user must have that set

    def get_category_by_id(self, category_id: str) -> Category | None:
        with ApiClient(self.config) as api_client:
            api_instance = CategoriesApi(api_client)

            try:
                api_response: CategoryResponse = api_instance.get_category_by_id(
                    self.budget_id, category_id
                )
                return api_response.data.category
            except Exception as e:
                print("Exception when calling CategoriesApi->get_categories: %s\n" % e)

    def get_categories_by_id(self, category_ids: list[str]) -> list[Category]:
        categories: list[Category] = []

        for id in category_ids:
            category  = self.get_category_by_id(id)
            if category is None:
                return None
            categories.append(category)

        return categories

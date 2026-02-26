from ynab import ApiClient, CategoriesApi, CategoryResponse, Configuration


class YNABClient:

    def __init__(self, access_token: str, budget_id: str):
        self.config = Configuration(access_token=access_token)
        self.budget_id = (
            budget_id if budget_id else "last-used"
        )  # could be 'default' but user must have that set

    def get_category_by_id(self, category_id: str):
        with ApiClient(self.config) as api_client:
            api_instance = CategoriesApi(api_client)

            try:
                api_response: CategoryResponse = api_instance.get_category_by_id(
                    self.budget_id, category_id
                )
                return api_response.data.category
            except Exception as e:
                print("Exception when calling CategoriesApi->get_categories: %s\n" % e)

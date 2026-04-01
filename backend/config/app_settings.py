from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import config.settings as settings # apps settings module
else:
    from django.conf import settings # Djano's LazySettings

from django.apps import AppConfig

import bs


class UserConfig(AppConfig):
    name = 'bs.core.user'

    def ready(self):
        import bs.core.user.signals

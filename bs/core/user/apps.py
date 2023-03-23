from django.apps import AppConfig

import bs


class UserConfig(AppConfig):
    name = 'bs.core.user'

    verbose_name = '账户'

    def ready(self):
        import bs.core.user.signals

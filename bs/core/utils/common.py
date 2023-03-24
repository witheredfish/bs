import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def import_from_settings(attr, *args):
    try:
        if args:
            return getattr(settings, attr, args[0])
        return getattr(settings, attr)
    except AttributeError:
        raise ImproperlyConfigured('未找到属性{0}'.format(attr))


def su_login_callback(user):

    if user.is_active and user.is_superuser:
        return True

    logger.warn('用户{}请求登录其他账号，没有权限，已驳回。', user)
    return False

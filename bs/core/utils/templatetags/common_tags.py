from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def settings_value(name):
    allowed_names = [
        'LOGIN_FAIL_MESSAGE',
        'ACCOUNT_CREATION_TEXT',
        'CENTER_NAME',
        'CENTER_HELP_URL',
        'EMAIL_PROJECT_REVIEW_CONTACT',
    ]
    return mark_safe(getattr(settings, name, '') if name in allowed_names else '')

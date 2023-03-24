import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from bs.core.utils.common import import_from_settings

logger = logging.getLogger(__name__)
EMAIL_ENABLED = import_from_settings('EMAIL_ENABLED', False)
EMAIL_SUBJECT_PREFIX = import_from_settings('EMAIL_SUBJECT_PREFIX')
EMAIL_DEVELOPMENT_EMAIL_LIST = import_from_settings(
    'EMAIL_DEVELOPMENT_EMAIL_LIST')
EMAIL_SENDER = import_from_settings('EMAIL_SENDER')
EMAIL_TICKET_SYSTEM_ADDRESS = import_from_settings(
    'EMAIL_TICKET_SYSTEM_ADDRESS')
EMAIL_OPT_OUT_INSTRUCTION_URL = import_from_settings(
    'EMAIL_OPT_OUT_INSTRUCTION_URL')
EMAIL_SIGNATURE = import_from_settings('EMAIL_SIGNATURE')
EMAIL_CENTER_NAME = import_from_settings('CENTER_NAME')
CENTER_BASE_URL = import_from_settings('CENTER_BASE_URL')


def send_email(subject, body, sender,  receiver_list, cc=[]):
    if not EMAIL_ENABLED:
        return

    if len(receiver_list) == 0:
        logger.error("发送失败，没有接收对象。")

    if len(sender) == 0:
        logger.error("发送失败，缺失发送地址。")

    if len(EMAIL_SUBJECT_PREFIX) > 0:
        subject = EMAIL_SUBJECT_PREFIX + '  '+subject

    if settings.DEBUG:
        receiver_list = EMAIL_DEVELOPMENT_EMAIL_LIST

    if cc and settings.DEBUG:
        cc = EMAIL_DEVELOPMENT_EMAIL_LIST

    try:
        if cc:
            email = EmailMessage(subject, body, sender,
                                 receiver_list, cc)
            email.send(fail_silently=False)
        else:
            send_mail(subject, body, sender,
                      receiver_list, fail_silently=False)

    except SMTPException as e:
        print(e)
        logger.error("主题为%s的邮件，从%s发给%s，发送失败了", subject,
                     sender, ','.join(receiver_list))


def send_email_template(subject, template_name, template_context, sender, receiver_list):
    if not EMAIL_ENABLED:
        return

    body = render_to_string(template_name, template_context)

    return send_email(subject, body, sender, receiver_list)

from bs.config.base import SETTINGS_EXPORT
from bs.config.env import ENV

CENTER_NAME = ENV.str('CENTER_NAME', default='HPC中心')
CENTER_HELP_URL = ENV.str('CENTER_HELP_URL', default='')
CENTER_PROJECT_RENAME_HELP_URL = ENV.str(
    'CENTER_PROJECT_RENAME_HELP_URL', default='')
CENTER_BASE_URL = ENV.str('CENTER_BASE_URL', default='')

PROJECT_ENABLE_PROJECT_REVIEW = ENV.bool(
    'PROJECT_ENABLE_PROJECT_REVIEW', default=True)

ALLOCATION_ENABLE_CHANGE_REQUESTS_BY_DEFAULT = ENV.bool(
    'ALLOCATION_ENABLE_CHANGE_REQUESTS', default=True)
ALLOCATION_CHANGE_REQUEST_EXTENSION_DAYS = ENV.list(
    'ALLOCATION_CHANGE_REQUEST_EXTENSION_DAYS', cast=int, default=[30, 60, 90])
ALLOCATION_ENABLE_ALLOCATION_RENEWAL = ENV.bool(
    'ALLOCATION_ENABLE_ALLOCATION_RENEWAL', default=True)
ALLOCATION_FUNCS_ON_EXPIRE = [
    'bs.core.allocation.utils.test_allocation_function', ]
ALLOCATION_DEFAULT_ALLOCATION_LENGTH = ENV.int(
    'ALLOCATION_DEFAULT_ALLOCATION_LENGTH', default=365)

ALLOCATION_ACCOUNT_ENABLED = ENV.bool(
    'ALLOCATION_ACCOUNT_ENABLED', default=False)
ALLOCATION_ACCOUNT_MAPPING = ENV.dict('ALLOCATION_ACCOUNT_MAPPING', default={})

SETTINGS_EXPORT += [
    'ALLOCATION_ACCOUNT_ENABLED',
    'CENTER_HELP_URL',
]

ADMIN_COMMENTS_SHOW_EMPTY = ENV.bool('ADMIN_COMMENTS_SHOW_EMPTY', default=True)

ALLOCATION_ATTRIBUTE_VIEW_LIST = ENV.list('ALLOCATION_ATTRIBUTE_VIEW_LIST', default=[
                                          'slurm_account_name', 'freeipa_group', 'Cloud Account Name', ])

INVOICE_ENABLED = ENV.bool('INVOICE_ENABLED', default=True)
INVOICE_DEFAULT_STATUS = ENV.str('INVOICE_DEFAULT_STATUS', default='New')

ONDEMAND_URL = ENV.str('ONDEMAND_URL', default=None)

LOGIN_FAIL_MESSAGE = ENV.str('LOGIN_FAIL_MESSAGE', default='登录失败')

EMAIL_DIRECTOR_PENDING_PROJECT_REVIEW_EMAIL = """
你最近申请了账户续订，但是你并没有在系统中输入任何出版物或资助信息。因此我不会批准你的续订请求。这些信息能够帮助我们拿到更多的资源，还请如实输入。

如果有任何问题，可以与我们联系。

谢谢，祝好。
电话:15061107827
"""

ACCOUNT_CREATION_TEXT = '所有人员能通过提供相关材料来申请账户。详情请查看<a href="https://github.com/witheredfish/bs">说明</a>。（只可用于教育，不可商用）'

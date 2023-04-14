import os
import sys
import bs
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from bs.config.env import ENV, PROJECT_ROOT

VERSION = bs.VERSION
BASE_DIR = PROJECT_ROOT()
ALLOWED_HOSTS = ENV.list('ALLOWED_HOSTS', default=['*'])
DEBUG = ENV.bool('DEBUG', default=True)
WSGI_APPLICATION = 'bs.config.wsgi.application'
ROOT_URLCONF = 'bs.config.urls'

SECRET_KEY = ENV.str('SECRET_KEY', default='')
if len(SECRET_KEY) == 0:
    SECRET_KEY = get_random_secret_key()

LANGUAGE_CODE = ENV.str('LANGUAGE_CODE', default='zh-hans')
TIME_ZONE = ENV.str('TIME_ZONE', default='Asia/Shanghai')
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

sys.modules['fontawesome_free'] = __import__('fontawesome-free')
INSTALLED_APPS += [
    'crispy_forms',
    'sslserver',
    'django_q',
    'simple_history',
    'fontawesome_free',
]

INSTALLED_APPS += [
    'bs.core.portal',
    'bs.core.user',
    'bs.core.utils',
    'bs.core.field_of_science',
    'bs.core.project',
    'bs.core.resource',
    'bs.core.grant',
    'bs.core.allocation',
    'bs.core.publication',
    'bs.core.research_output',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

AUTHENTICATION_BACKENDS = []

Q_CLUSTER = {
    'timeout': ENV.int('Q_CLUSTER_TIMEOUT', default=120),
    'retry': ENV.int('Q_CLUSTER_RETRY', default=120),
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            PROJECT_ROOT('site/templates'),
            '/usr/share/bs/site/templates',
            PROJECT_ROOT('bs/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
            ],
        },
    },
]

SITE_TEMPLATES = ENV.str('SITE_TEMPLATES', default='')
if len(SITE_TEMPLATES) > 0:
    if os.path.isdir(SITE_TEMPLATES):
        TEMPLATES[0]['DIRS'].insert(0, SITE_TEMPLATES)
    else:
        raise ImproperlyConfigured(
            'SITE_TEMPLATES地址错误')

CRISPY_TEMPLATE_PACK = 'bootstrap4'
SETTINGS_EXPORT = []

STATIC_URL = '/static/'
STATIC_ROOT = ENV.str('STATIC_ROOT', default=PROJECT_ROOT('static_root'))
STATICFILES_DIRS = [
    PROJECT_ROOT('bs/static'),
]

SITE_STATIC = ENV.str('SITE_STATIC', default='')
if len(SITE_STATIC) > 0:
    if os.path.isdir(SITE_STATIC):
        STATICFILES_DIRS.insert(0, SITE_STATIC)
    else:
        raise ImproperlyConfigured(
            'SITE_STATIC地址错误')

if os.path.isdir('/usr/share/bs/site/static'):
    STATICFILES_DIRS.insert(0, '/usr/share/bs/site/static')

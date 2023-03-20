import environ
from split_settings.tools import optional, include
from bs.config.env import ENV, PROJECT_ROOT

bs_configs = [
    'base.py',
    'database.py',
    'auth.py',
    'logging.py',
    'core.py',
    'email.py',
]

plugin_configs = {

}

for key, pc in plugin_configs.items():
    if ENV.bool(key, default=False):
        bs_configs.append(pc)

local_configs = [
    'local_settings.py',
    '/etc/bs/local_settings.py',
    PROJECT_ROOT('local_settings.py')
]

if ENV.str('BS_CONFIG', default='') != '':
    local_configs.append(environ.Path(ENV.str('BS_CONFIG'))())

for lc in local_configs:
    bs_configs.append(optional(lc))

include(*bs_configs)

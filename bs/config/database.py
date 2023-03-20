import os
from bs.config.env import ENV

DATABASES = {
    'default': ENV.db_url(
        var='DB_URL',
        default='sqlite:///'+os.path.join(os.getcwd(), 'bs.db')
    )
}

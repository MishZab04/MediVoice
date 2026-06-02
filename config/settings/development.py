from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
}

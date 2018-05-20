import sys

from .common import *

DEBUG=True
TEMPLATE_DEBUG=DEBUG

secrets = load_secrets('dev_secrets.json')
SECRET_KEY = get_secret("SECRET_KEY", secrets)


# Needed to share URL across the network
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': get_secret("DEFAULT_DB_NAME", secrets),
        'USER': get_secret("DEFAULT_DB_USER", secrets),
        'PASSWORD': get_secret("DEFAULT_DB_PASSWORD", secrets),
        'HOST': 'localhost',
        'PORT': get_secret("DEFAULT_DB_PORT", secrets),
    },
}
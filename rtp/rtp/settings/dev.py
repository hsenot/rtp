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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'DEBUG',
        'handlers': [
            'console',
        ],
    },
    'formatters': {
        'verbose': {
            'format': "%(name)s %(filename)s line %(lineno)d [%(asctime)s] %(levelname)s %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'urllib3': {
            'handlers': [],
            'level': 'INFO',
            'propagate': False,
        },
        'requests': {
            'handlers': [],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

APIS = get_secret("APIS", secrets)

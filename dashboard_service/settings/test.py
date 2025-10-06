from .common import *  # noqa

DEBUG = True

ALLOWED_HOSTS = [".localhost", "127.0.0.1"]

ENV = "test"

SECRET_KEY = "test-secret-key"


AUTH0_CLIENT_ID = "test-client-id"
AUTH0_DOMAIN = "test.eu.auth0.com"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
}

STORAGES["staticfiles"] = {  # noqa
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}

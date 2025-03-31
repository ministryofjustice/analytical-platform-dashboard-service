from .common import *  # noqa

DEBUG = True

ALLOWED_HOSTS = [".localhost", "127.0.0.1"]

ENV = "local"

SECRET_KEY = "django-insecure-p)0zsf0h@(4$exs814m35ly%x_m8z)z!11n(z^sfl01nsfr+!r"

INSTALLED_APPS += [  # noqa
    "debug_toolbar",
]

MIDDLEWARE += [  # noqa
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

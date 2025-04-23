from socket import gethostbyname, gethostname

from .common import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = ["dashboards.analytical-platform.service.justice.gov.uk"]

ALLOWED_HOSTS.append(gethostbyname(gethostname()))

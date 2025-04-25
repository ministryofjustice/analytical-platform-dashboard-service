from socket import gethostbyname, gethostname

from .common import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = ["dashboards.analytical-platform.service.justice.gov.uk"]

ALLOWED_HOSTS.append(gethostbyname(gethostname()))

AUTH0_DOMAIN = "alpha-analytics-moj.eu.auth0.com"
AUTH0_AUDIENCE = "urn:control-panel-prod-api"

CONTROL_PANEL_API_URL = (
    "https://controlpanel.services.analytical-platform.service.justice.gov.uk/api/cpanel/v1/"
)
